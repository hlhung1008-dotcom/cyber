// 鴨答角色完整匯出腳本
// 在 caveduck.io 任一頁面（建議 /zh-hant/creates/characters）用 javascript_tool 執行。
// 會在背景跑，進度看 window.__EXLOG，完成後自動下載 caveduck_full_backup.json。
// 分頁在背景時瀏覽器會降速，盡量讓這個分頁保持在前景。
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  window.__EX = []; window.__EXLOG = [];

  // 1. 從創作頁找出全部角色 uuid
  const list = document.createElement('iframe');
  list.style.cssText = 'position:fixed;left:-3000px;top:0;width:1200px;height:4000px';
  list.src = '/zh-hant/creates/characters';
  document.body.appendChild(list);
  await new Promise(r => list.onload = r); await sleep(4000);
  // 往下捲動幾次，確保角色卡全部載入
  for (let i = 0; i < 6; i++) { list.contentWindow.scrollTo(0, 99999); await sleep(800); }
  const ids = [];
  list.contentDocument.querySelectorAll('a[href]').forEach(a => {
    const m = a.getAttribute('href').match(/\/characters\/(?:edit\/|new\/)?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/);
    if (m && !ids.includes(m[1])) ids.push(m[1]);
  });
  list.remove();
  window.__UU = ids; __EXLOG.push('找到 ' + ids.length + ' 個角色');

  // 2. 逐一讀取每個角色的編輯頁
  const grabAll = async (u) => {
    const f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:-3000px;top:0;width:1200px;height:900px';
    f.src = '/zh-hant/characters/edit/' + u + '?v=' + Date.now();
    document.body.appendChild(f);
    await new Promise(r => f.onload = r); await sleep(3500);
    const d = f.contentDocument;
    const vis = s => [...d.querySelectorAll(s)].filter(e => e.offsetParent);
    const grab = () => ({
      fields: vis('textarea,input').filter(e => !['file', 'checkbox', 'radio', 'hidden'].includes(e.type))
        .map(e => ({ ph: (e.placeholder || '').slice(0, 40), tag: e.tagName, v: e.value })),
      combos: vis('[role=combobox]').map(e => e.textContent.trim()),
      switches: vis('[role=switch]').map(e => e.getAttribute('aria-checked')),
      checked: vis('[role=checkbox][aria-checked=true],input[type=checkbox]:checked').map(e => e.getAttribute('aria-label') || e.name || '')
    });
    const out = { uuid: u, name: '', tabs: {} };
    for (const t of ['個人資訊', '劇情', '對話範例', '內容']) {
      const b = [...d.querySelectorAll('main button')].find(x => x.textContent.trim() === t);
      if (!b) continue; b.click(); await sleep(1800);
      if (t === '劇情') {
        // 多劇情：每個「劇情 N」都要點開讀；隱藏的劇情面板也在 DOM 裡，所以只讀看得到的欄位
        out.tabs[t] = [];
        for (const sb of [...d.querySelectorAll('button')].filter(b => /^劇情\s*\d+$/.test(b.textContent.trim()))) {
          sb.click(); await sleep(1600);
          out.tabs[t].push({ label: sb.textContent.trim(), ...grab() });
        }
      } else out.tabs[t] = grab();
    }
    const nm = (out.tabs['個人資訊']?.fields || []).find(x => x.ph.startsWith('請輸入角色名稱'));
    out.name = nm ? nm.v : '';
    // 可見性分頁只讀「創作者評論」，不碰任何設定
    const vb = [...d.querySelectorAll('main button')].find(x => x.textContent.trim() === '可見性');
    if (vb) { vb.click(); await sleep(1800); const c = vis('textarea[placeholder^="在此處為使用者留下訊息"]')[0]; out.comment = c ? c.value : null; }
    f.remove(); return out;
  };

  for (const u of ids) {
    try { const o = await grabAll(u); __EX.push(o); __EXLOG.push((o.name || u.slice(0, 8)) + ':' + (o.tabs['劇情'] || []).length); }
    catch (e) { __EXLOG.push(u.slice(0, 8) + ' ERR ' + e.message); }
  }

  // 3. 下載
  const bl = new Blob([JSON.stringify({ exportedAt: new Date().toISOString(), chars: __EX })], { type: 'application/json' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(bl); a.download = 'caveduck_full_backup.json';
  document.body.appendChild(a); a.click(); a.remove();
  __EXLOG.push('DONE ' + __EX.length + ' 個角色，' + bl.size + ' bytes');
})();
'started';
