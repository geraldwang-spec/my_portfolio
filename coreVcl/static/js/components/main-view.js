/* =========================================================
 * components/main-view.js — 決定主畫面顯示 AI 對話或工具畫面
 * ---------------------------------------------------------
 * 選單沒有 type（或 type: 'chat'）→ AI 對話
 * 其他 type → 從 views/index.js 找到對應模組，動態載入後 mount
 * ========================================================= */
import { getNav, currentKey } from '../core/state.js';
import { on } from '../core/events.js';
import { views } from '../views/index.js';
import { esc } from '../utils/dom.js';
import { renderChat } from './chat.js';

let chatView, toolView;
let current = null;   // { key, unmount }

export function initMainView() {
  chatView = document.getElementById('chatView');
  toolView = document.getElementById('toolView');
  on('navigate', render);
  on('history-cleared', render);
  render();
}

function render() {
  const nav = getNav();
  if (nav?.type && nav.type !== 'chat') {
    chatView.hidden = true;
    toolView.hidden = false;
    mountTool(nav);
  } else {
    unmountTool();
    toolView.hidden = true;
    chatView.hidden = false;
    renderChat();
  }
}

async function mountTool(nav) {
  const key = currentKey();
  if (current?.key === key) return;   // 同一個畫面不重新掛載
  unmountTool();

  const entry = { key, unmount: null };
  current = entry;
  const loader = views[nav.type];
  if (!loader) {
    toolView.innerHTML = `<div class="empty"><h2>找不到畫面「${esc(nav.type)}」</h2>
      <p>請在 js/views/index.js 註冊這個畫面類型。</p></div>`;
    return;
  }

  toolView.innerHTML = '<div class="empty"><p>載入中…</p></div>';
  try {
    const mod = await loader();
    if (current !== entry) return;             // 載入期間已切到別的選單
    const unmount = await mod.mount(toolView, nav);
    if (current !== entry) { unmount?.(); return; }
    entry.unmount = unmount;
  } catch (err) {
    console.error(err);
    if (current === entry) {
      toolView.innerHTML = `<div class="empty"><h2>畫面載入失敗</h2>
        <p>${esc(err.message)}。請重新整理頁面後再試一次。</p></div>`;
    }
  }
}

function unmountTool() {
  if (!current) return;
  try { current.unmount?.(); } catch (err) { console.error(err); }
  current = null;
  toolView.innerHTML = '';
}
