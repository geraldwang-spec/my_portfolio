/* =========================================================
 * components/account.js — sidebar 底部的登入 / 使用者 / 登出
 * ---------------------------------------------------------
 * 登入、註冊、忘記密碼都在 auth-dialog.js 的登入視窗裡完成
 * ========================================================= */
import { state } from '../core/state.js';
import { on } from '../core/events.js';
import * as auth from '../services/auth-api.js';
import { esc, icon } from '../utils/dom.js';
import { openAuth } from './auth-dialog.js';

let slot;

export function initAccount() {
  slot = document.getElementById('accountSlot');
  slot.innerHTML = '<div class="account-loading" aria-label="讀取登入狀態"><span></span><span></span></div>';

  slot.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    if (btn.dataset.action === 'login') openAuth('login');
    if (btn.dataset.action === 'logout') logout(btn);
  });

  let changedByUser = false;
  on('user-changed', (user) => { changedByUser = true; state.user = user; render(); });

  // 頁面載入時向後端詢問登入狀態（不依賴模板把資料寫進頁面）
  auth.fetchCurrentUser().then((user) => {
    if (changedByUser) return;          // 查詢期間使用者已在視窗登入，以那次為準
    state.user = user;
    render();
  });
}

function render() {
  const u = state.user;
  slot.innerHTML = u ? `
    <div class="account" data-tip="${esc(u.name)}" tabindex="0" title="${esc(u.email || u.name)}">
      <span class="acct-avatar" aria-hidden="true">${esc(u.name.charAt(0).toUpperCase())}</span>
      <span class="label acct-info"><b>${esc(u.name)}</b>${u.email ? `<small>${esc(u.email)}</small>` : ''}</span>
    </div>
    <button class="foot-item" data-action="logout" data-tip="登出">
      ${icon('logout')}<span class="label">登出</span>
    </button>
    <p class="foot-error" role="alert" hidden></p>` : `
    <button class="foot-item login" data-action="login" data-tip="登入">
      ${icon('login')}<span class="label">登入</span>
    </button>`;
}

async function logout(btn) {
  const label = btn.querySelector('.label');
  const err = slot.querySelector('.foot-error');
  btn.disabled = true;
  label.textContent = '登出中…';
  err.hidden = true;
  try {
    await auth.logout();
    state.user = null;
    render();
  } catch (e) {
    btn.disabled = false;
    label.textContent = '登出';
    err.textContent = e.message;
    err.hidden = false;
  }
}
