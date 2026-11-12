/* =========================================================
 * views/production/index.js — 卡控首頁
 * ---------------------------------------------------------
 * 進入畫面時向後端要目前工作區的資料：
 *   GET /production/workspaces/{state.workspaceId}/home
 * ========================================================= */
import { state } from '../../core/state.js';
import * as production from '../../services/production-api.js';
import { esc } from '../../utils/dom.js';

/**
 * @param {HTMLElement} root 主畫面容器（main-view.js 傳進來的 toolView）
 * @param {object} nav       config.js 裡這個選單項目的設定
 * @returns {Promise<() => void>} unmount：離開畫面時呼叫
 */
export async function mount(root, nav) {
  // 沒登入就沒有工作區，不用打 API
  if (state.workspaceId == null) {
    root.innerHTML = `<div class="empty"><h2>${esc(nav.title)}</h2><p>請先登入。</p></div>`;
    return () => { };
  }

  root.innerHTML = '<div class="empty"><p>載入中…</p></div>';
  try {
    const home = await production.fetchHome();          // ← 上一則那段放在這裡
    root.innerHTML = `
      <div class="empty">
        <h2>${esc(nav.title)}</h2>
        <p>目前工作區：${esc(home.workspace ?? '')}</p>
      </div>`;
  } catch (err) {
    root.innerHTML = `<div class="empty"><h2>${esc(nav.title)}</h2><p>${esc(err.message)}</p></div>`;
  }

  return () => { };    // 目前沒有計時器或事件要清，回傳空的 unmount
}
