/* =========================================================
 * views/index.js — 工具畫面註冊表
 * ---------------------------------------------------------
 * key 對應 config.js 選單的 type，value 是動態載入函式。
 * 使用 import() 動態載入：只有使用者進入該畫面時才下載程式碼。
 *
 * 新增畫面：
 *   1. 建立 views/<名稱>/index.js，export async function mount(root, nav) { ...; return unmount; }
 *   2. 在下方加一行
 *   3. config.js 的選單設定 type: '<名稱>'
 * ========================================================= */
export const views = {
  cie1931: () => import('./cie1931/index.js')
};
