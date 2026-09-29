/* =========================================================
 * components/auth-dialog.js — 登入視窗
 * ---------------------------------------------------------
 * 一個視窗裡切換六個畫面（同原本 login.html 的 data-view 做法）：
 *
 *   login ⇄ register              上方分頁切換
 *   login → forgot → sent         忘記密碼 → 寄出重設信
 *   信中連結 → reset → login       設定新密碼後回到登入
 *   信中連結失效 → invalid → forgot
 *
 * 表單欄位名稱與原本的 login.html 相同，後端不用改。
 * ========================================================= */
import config from '../config.js';
import { emit } from '../core/events.js';
import * as auth from '../services/auth-api.js';
import { icon, collectRefs } from '../utils/dom.js';
import { closeMobileMenu } from './sidebar.js';

const MIN = config.auth?.passwordMinLength ?? 6;
const COOLDOWN = config.auth?.resendCooldown ?? 60;
const isMock = () => config.auth?.mode === 'mock';

let dlg, R;
let lastResetRequest = null;   // 重新寄送用
let cooldownTimer = 0;

/* ---------- HTML ---------- */
const field = (label, name, type, extra = '') => `
  <label class="field">
    <span>${label}</span>
    <input name="${name}" id="${name}" type="${type}" required ${extra}>
  </label>`;

const head = (title, back = '') => `
  <div class="modal-head">
    <h2 class="auth-title">${back}${title}</h2>
    <button type="button" class="close-btn" data-close aria-label="關閉">${icon('close')}</button>
  </div>`;

const backBtn = `<button type="button" class="auth-back" data-go="login" aria-label="返回登入">${icon('back')}</button>`;

const tabs = (active) => `
  <div class="auth-tabs" role="tablist">
    <button type="button" role="tab" aria-selected="${active === 'login'}" data-go="login">登入</button>
    <button type="button" role="tab" aria-selected="${active === 'register'}" data-go="register">註冊</button>
  </div>`;

function template() {
  return `
  <div class="modal-body panel auth-card" data-view="login">

    <form class="auth-view" data-auth-view="login" novalidate>
      ${head('歡迎回來')}
      ${tabs('login')}
      <p class="auth-notice" data-ref="loginNotice" role="status" hidden></p>
      ${field('帳號', 'login-username', 'text', 'autocomplete="username"')}
      ${field('密碼', 'login-password', 'password', 'autocomplete="current-password"')}
      <div class="auth-row"><button type="button" class="text-link" data-go="forgot">忘記密碼？</button></div>
      <p class="form-error" role="alert"></p>
      <button type="submit" class="primary-btn block">登入</button>
    </form>

    <form class="auth-view" data-auth-view="register" novalidate hidden>
      ${head('建立帳號')}
      ${tabs('register')}
      ${field('帳號', 'register-username', 'text', 'autocomplete="username"')}
      ${field('E-mail', 'register-email', 'email', 'autocomplete="email" placeholder="name@example.com"')}
      ${field(`密碼（至少 ${MIN} 個字元）`, 'register-password', 'password', `autocomplete="new-password" minlength="${MIN}"`)}
      ${field('確認密碼', 'register-repeat', 'password', 'autocomplete="new-password"')}
      <p class="form-error" role="alert"></p>
      <button type="submit" class="primary-btn block">建立帳號</button>
    </form>

    <form class="auth-view" data-auth-view="forgot" novalidate hidden>
      ${head('忘記密碼', backBtn)}
      <p class="auth-desc">輸入帳號與註冊時的 E-mail，我們會寄一封重設密碼的信給你。</p>
      ${field('帳號', 'reset-username', 'text', 'autocomplete="username"')}
      ${field('E-mail', 'reset-email', 'email', 'autocomplete="email" placeholder="name@example.com"')}
      <p class="form-error" role="alert"></p>
      <button type="submit" class="primary-btn block">寄送重設密碼信</button>
    </form>

    <div class="auth-view" data-auth-view="sent" hidden>
      ${head('請到信箱收信', backBtn)}
      <div class="auth-hero">${icon('mail')}</div>
      <p class="auth-desc center">重設密碼的連結已寄到<br><b data-ref="sentEmail"></b></p>
      <p class="auth-desc small center">點信中的連結即可設定新密碼。沒收到信的話，請先檢查垃圾郵件匣。</p>
      <p class="auth-notice" data-ref="sentNotice" role="status" hidden></p>
      <p class="form-error" data-ref="sentError" role="alert"></p>
      <div class="auth-actions">
        <button type="button" class="ghost-btn" data-ref="resend">重新寄送</button>
        <button type="button" class="primary-btn" data-go="login">返回登入</button>
      </div>
      ${isMock() ? '<button type="button" class="text-link center" data-go="reset">（示範）直接開啟信中的重設密碼連結</button>' : ''}
    </div>

    <form class="auth-view" data-auth-view="reset" novalidate hidden>
      ${head('設定新密碼')}
      <div class="auth-hero small">${icon('key')}</div>
      ${field(`新密碼（至少 ${MIN} 個字元）`, 'reset-pw-password', 'password', `autocomplete="new-password" minlength="${MIN}"`)}
      ${field('確認新密碼', 'reset-pw-repeat', 'password', 'autocomplete="new-password"')}
      <p class="form-error" role="alert"></p>
      <button type="submit" class="primary-btn block">更新密碼</button>
    </form>

    <div class="auth-view" data-auth-view="invalid" hidden>
      ${head('連結已失效')}
      <div class="auth-hero warn">${icon('alert')}</div>
      <p class="auth-desc center">這個重設密碼的連結已經使用過或已過期。<br>請重新申請一次。</p>
      <div class="auth-actions">
        <button type="button" class="ghost-btn" data-go="login">返回登入</button>
        <button type="button" class="primary-btn" data-go="forgot">重新申請</button>
      </div>
    </div>

  </div>`;
}

/* ---------- 初始化 ---------- */
export function initAuthDialog() {
  dlg = document.getElementById('authDlg');
  dlg.innerHTML = template();
  R = collectRefs(dlg);
  R.card = dlg.querySelector('.auth-card');
  dlg.querySelectorAll('[data-auth-view]').forEach((v) => {
    v.querySelector('.auth-title').id = `authTitle-${v.dataset.authView}`;
  });

  dlg.addEventListener('click', (e) => {
    if (e.target.closest('[data-close]')) { dlg.close(); return; }
    const go = e.target.closest('[data-go]');
    if (go) showView(go.dataset.go);
  });
  dlg.addEventListener('close', () => clearInterval(cooldownTimer));

  const form = (name) => dlg.querySelector(`[data-auth-view="${name}"]`);
  onSubmit(form('login'), handleLogin);
  onSubmit(form('register'), handleRegister);
  onSubmit(form('forgot'), handleForgot);
  onSubmit(form('reset'), handleReset);
  R.resend.addEventListener('click', handleResend);

  matchPasswords('register-password', 'register-repeat');
  matchPasswords('reset-pw-password', 'reset-pw-repeat');

  openFromUrl();
}

/**
 * 打開登入視窗
 * @param {'login'|'register'|'forgot'|'sent'|'reset'|'invalid'} view
 */
export function openAuth(view = 'login') {
  showView(view);
  if (!dlg.open) dlg.showModal();
  closeMobileMenu();
  focusFirst();
}

/* 信中連結會導向 /?auth=reset 或 /?auth=reset-invalid */
function openFromUrl() {
  const url = new URL(window.location.href);
  const param = url.searchParams.get('auth');
  if (!param) return;
  const map = { login: 'login', register: 'register', forgot: 'forgot', reset: 'reset', 'reset-invalid': 'invalid' };
  url.searchParams.delete('auth');
  history.replaceState(null, '', url.pathname + url.search + url.hash);
  if (map[param]) openAuth(map[param]);
}

/* ---------- 畫面切換 ---------- */
function showView(view, { notice = '', keep = false } = {}) {
  R.card.dataset.view = view;
  dlg.querySelectorAll('[data-auth-view]').forEach((v) => {
    const on = v.dataset.authView === view;
    v.hidden = !on;
    if (!on && !keep) resetView(v);
  });
  dlg.setAttribute('aria-labelledby', `authTitle-${view}`);

  if (view === 'login') setNotice(R.loginNotice, notice);
  if (dlg.open) focusFirst();
}

function resetView(v) {
  if (v.tagName === 'FORM') v.reset();
  v.querySelectorAll('.form-error').forEach((p) => { p.textContent = ''; });
}

function focusFirst() {
  const active = dlg.querySelector('[data-auth-view]:not([hidden])');
  (active.querySelector('input') || active.querySelector('.primary-btn'))?.focus();
}

function setNotice(el, text) {
  el.textContent = text;
  el.hidden = !text;
}

/* ---------- 表單送出（對應原本 auth-share.js 的 submitForm） ---------- */
function onSubmit(form, handler) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const error = form.querySelector('.form-error');
    error.textContent = '';
    if (!form.checkValidity()) {
      const bad = form.querySelector(':invalid');
      error.textContent = validationMessage(bad);
      bad.focus();
      return;
    }
    const btn = form.querySelector('[type="submit"]');
    const label = btn.textContent;
    btn.disabled = true;
    btn.textContent = '處理中…';
    try {
      await handler(Object.fromEntries(new FormData(form)), form);
    } catch (err) {
      error.textContent = err.message;
    } finally {
      btn.disabled = false;
      btn.textContent = label;
    }
  });
}

/** 把瀏覽器的驗證結果轉成中文訊息，顯示在表單內 */
function validationMessage(input) {
  const name = input.closest('.field')?.querySelector('span')?.textContent.replace(/（.*）/, '') || '這個欄位';
  const v = input.validity;
  if (v.valueMissing) return `請輸入${name}。`;
  if (v.typeMismatch) return 'E-mail 格式不正確，請重新輸入。';
  if (v.tooShort) return `密碼至少需要 ${MIN} 個字元。`;
  if (v.customError) return input.validationMessage;
  return `${name}格式不正確，請重新輸入。`;
}

/** 兩個密碼欄位需一致（對應原本 auth-share.js 的 initPasswordMatch） */
function matchPasswords(passwordName, repeatName) {
  const pw = dlg.querySelector(`[name="${passwordName}"]`);
  const rep = dlg.querySelector(`[name="${repeatName}"]`);
  const check = () => rep.setCustomValidity(rep.value && rep.value !== pw.value ? '兩次輸入的密碼不一致。' : '');
  pw.addEventListener('input', check);
  rep.addEventListener('input', check);
}

/* ---------- 各畫面的動作 ---------- */
async function handleLogin(data) {
  const user = await auth.login(data);
  dlg.close();
  resetView(dlg.querySelector('[data-auth-view="login"]'));
  setNotice(R.loginNotice, '');
  emit('user-changed', user);
}

async function handleRegister(data) {
  const message = await auth.register(data);
  showView('login', { notice: message });
  dlg.querySelector('[name="login-username"]').value = data['register-username'];
  dlg.querySelector('[name="login-password"]').focus();
}

async function handleForgot(data) {
  await auth.requestReset(data);
  lastResetRequest = data;
  R.sentEmail.textContent = data['reset-email'];
  setNotice(R.sentNotice, '');
  R.sentError.textContent = '';
  showView('sent', { keep: true });
  startCooldown();
}

async function handleResend() {
  if (!lastResetRequest) return;
  R.sentError.textContent = '';
  setNotice(R.sentNotice, '');
  R.resend.disabled = true;
  R.resend.textContent = '寄送中…';
  try {
    await auth.requestReset(lastResetRequest);
    setNotice(R.sentNotice, '已重新寄出，請再檢查一次信箱。');
    startCooldown();
  } catch (err) {
    R.sentError.textContent = err.message;
    R.resend.disabled = false;
    R.resend.textContent = '重新寄送';
  }
}

function startCooldown() {
  clearInterval(cooldownTimer);
  let left = COOLDOWN;
  const tick = () => {
    R.resend.disabled = left > 0;
    R.resend.textContent = left > 0 ? `重新寄送（${left}）` : '重新寄送';
    left -= 1;
    if (left < -1) clearInterval(cooldownTimer);
  };
  tick();
  cooldownTimer = setInterval(tick, 1000);
}

async function handleReset(data) {
  const message = await auth.renewPassword(data);
  showView('login', { notice: message });
}

