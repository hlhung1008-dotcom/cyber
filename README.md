# 加密備份

`caveduck_backup.7z` 是加密壓縮檔（AES-256，檔名也加密）。

用 7-Zip 開啟並輸入密碼即可解壓。沒有密碼無法看到任何內容。

## tools/

- `export.js`：在 caveduck.io 頁面執行，匯出全部角色並下載 `caveduck_full_backup.json`。
- `convert.py`：把匯出檔轉成資料庫格式、可閱讀資料夾與加密 7z。
這兩個檔案不含任何角色內容。
