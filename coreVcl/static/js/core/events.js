/* =========================================================
 * core/events.js — 簡單的事件匯流排
 * ---------------------------------------------------------
 * 讓各元件不用互相 import 就能溝通，例如：
 *   sidebar 切換選單 → emit('navigate') → 主畫面、位置列各自更新
 *
 * 目前使用的事件：
 *   navigate         切換主題或選單
 *   history-cleared  對話紀錄被清除
 *   api-changed      API 設定變更
 *   user-changed     登入成功（detail 為使用者）
 * ========================================================= */
const listeners = new Map();

/** 訂閱事件，回傳取消訂閱的函式 */
export function on(type, fn) {
  if (!listeners.has(type)) listeners.set(type, new Set());
  listeners.get(type).add(fn);
  return () => listeners.get(type)?.delete(fn);
}

export function emit(type, detail) {
  listeners.get(type)?.forEach((fn) => {
    try { fn(detail); } catch (err) { console.error(`[${type}]`, err); }
  });
}
