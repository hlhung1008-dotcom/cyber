#!/usr/bin/env python3
"""鴨答完整備份：把 export.js 下載的 caveduck_full_backup.json 轉成各種備份格式。

用法：
  python3 convert.py RAW_JSON OUT_DIR PASSWORD [WIDGET_DIR]

產出（都在 OUT_DIR）：
  db.json                         角色資料庫格式（每個角色一個欄位清單）
  data.js                         給「鴨答角色資料庫」網頁用的資料檔（window.FULLDATA）
  鴨答備份_YYYY-MM-DD/            可閱讀版：每個角色一個資料夾、每個欄位一個檔案、總覽.txt
  caveduck_backup_YYYY-MM-DD.7z   上面整個資料夾的加密壓縮（AES-256，檔名也加密）
需要：pip install py7zr --break-system-packages
"""
import json, os, re, shutil, sys

raw_path, out_dir, password = sys.argv[1], sys.argv[2], sys.argv[3]
widget_dir = sys.argv[4] if len(sys.argv) > 4 else None
os.makedirs(out_dir, exist_ok=True)
d = json.load(open(raw_path, encoding='utf-8'))
day = d['exportedAt'][:10]

def g(fields, prefix):
    for f in fields:
        if f['ph'].startswith(prefix):
            return f['v']
    return ''

chars = []
for order, c in enumerate(d['chars']):
    T = c['tabs']; P = T.get('個人資訊', {}).get('fields', [])
    name = g(P, '請輸入角色名稱') or g(P, '請輸入模擬器名稱') or c.get('name') or c['uuid'][:8]
    F = []
    def add(key, label, kind, v):
        F.append({'key': key, 'label': label, 'kind': kind, 'order': len(F), 'value': v})
    add('desc', '角色描述', 'text', g(P, '請描述該角色'))
    add('world', '世界觀', 'text', g(P, '請描述角色所屬的世界'))
    add('intro', '角色介紹(顯示描述)', 'html', g(P, '請輸入要向使用者顯示'))
    add('basic', '基本設定（類型、語言、世界觀選擇）', 'text', '\n'.join(T.get('個人資訊', {}).get('combos', [])))
    for i, s in enumerate(T.get('劇情', []), 1):
        f = s['fields']
        add(f's{i}_title', f'劇情{i}・標題', 'text', g(f, '請輸入標題'))
        add(f's{i}_open', f'劇情{i}・開場', 'text', g(f, '請撰寫劇情內容'))
        add(f's{i}_secret', f'劇情{i}・秘密', 'text', g(f, '這是應用於劇情的角色秘密'))
        add(f's{i}_style', f'劇情{i}・文風指南', 'text', g(f, '請指定角色的說話方式'))
        add(f's{i}_persona', f'劇情{i}・用戶畫像指南', 'text', g(f, '請輸入用戶畫像指南'))
        add(f's{i}_setting', f'劇情{i}・設定（小工具、骰子等）', 'text',
            '下拉選單：' + (' / '.join(s['combos']) or '無') + '\n開關：' + ' '.join(s['switches']))
    df = T.get('對話範例', {}).get('fields', [])
    us = [x['v'] for x in df if x['ph'].startswith('請輸入使用者可能會傳送的訊息')]
    cs = [x['v'] for x in df if x['ph'].startswith('請輸入角色的答覆')]
    add('dialog', f'對話範例（{len(us)} 組）', 'text',
        '\n\n'.join(f'【第{k+1}組】\n玩家：{a}\n角色：{b}' for k, (a, b) in enumerate(zip(us, cs))))
    add('oneline', '一句話介紹', 'text', g(P, '請輸入一句話'))
    add('comment', '創作者評論', 'html', c.get('comment') or '')
    alb = [x['v'] for x in T.get('內容', {}).get('fields', []) if x['ph'].startswith('請輸入圖片描述')]
    add('album', '相簿圖片描述', 'text', '\n'.join(f'{k+1}. {v}' for k, v in enumerate(alb)))
    chars.append({'uuid': c['uuid'], 'name': name, 'order': order, 'updatedAt': d['exportedAt'], 'fields': F})

# 同名角色加上 uuid 前綴區分
seen = {}
for c in chars:
    seen.setdefault(c['name'], []).append(c)
for n, group in seen.items():
    if len(group) > 1:
        for c in group[1:]:
            c['name'] = f"{n}（{c['uuid'][:4]}）"

json.dump(chars, open(f'{out_dir}/db.json', 'w', encoding='utf-8'), ensure_ascii=False)
open(f'{out_dir}/data.js', 'w', encoding='utf-8').write(
    'window.FULLDATA=' + json.dumps(chars, ensure_ascii=False).replace('</', '<\\/') + ';\n')

root = f'{out_dir}/鴨答備份_{day}'
shutil.rmtree(root, ignore_errors=True); os.makedirs(root)
safe = lambda s: re.sub(r'[\\/:*?"<>|]', '_', s)
idx = ['鴨答角色完整備份 ' + d['exportedAt'], '']
for c in chars:
    dn = safe(c['name']) + '_' + c['uuid'][:8]; os.makedirs(f'{root}/{dn}')
    idx.append(f"{c['name']}  https://caveduck.io/zh-hant/characters/edit/{c['uuid']}")
    for f in c['fields']:
        ext = '.html' if f['kind'] == 'html' else '.txt'
        open(f"{root}/{dn}/{f['order']:02d}_{safe(f['label'])}{ext}", 'w', encoding='utf-8').write(f['value'])
        idx.append(f"  {f['label']}：{len(f['value'])} 字")
    idx.append('')
open(f'{root}/總覽.txt', 'w', encoding='utf-8').write('\n'.join(idx))
shutil.copy(f'{out_dir}/db.json', f'{root}/全部角色資料.json')
shutil.copy(raw_path, f'{root}/原始匯出.json')
if widget_dir and os.path.isdir(widget_dir):
    os.makedirs(f'{root}/小工具', exist_ok=True)
    for fn in os.listdir(widget_dir):
        if os.path.isfile(os.path.join(widget_dir, fn)) and (fn.endswith('_states.json') or fn.endswith('_widget.html')):
            shutil.copy(os.path.join(widget_dir, fn), f'{root}/小工具/{fn}')

import py7zr
z = f'{out_dir}/caveduck_backup_{day}.7z'
if os.path.exists(z):
    os.remove(z)
with py7zr.SevenZipFile(z, 'w', password=password, header_encryption=True,
                        filters=[{'id': py7zr.FILTER_LZMA2}, {'id': py7zr.FILTER_CRYPTO_AES256_SHA256}]) as a:
    a.writeall(root, os.path.basename(root))
with py7zr.SevenZipFile(z, 'r', password=password) as a:
    a.testzip(); n = len(a.getnames())

print(json.dumps({'chars': len(chars),
                  'multi_scenario': {c['name']: sum(1 for f in c['fields'] if f['key'].endswith('_title')) for c in chars
                                     if sum(1 for f in c['fields'] if f['key'].endswith('_title')) > 1},
                  'total_chars': sum(len(f['value']) for c in chars for f in c['fields']),
                  'archive': z, 'archive_files': n, 'day': day}, ensure_ascii=False))
