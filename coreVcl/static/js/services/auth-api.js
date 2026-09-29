/* =========================================================
 * services/auth-api.js — 帳號相關 API
 * ---------------------------------------------------------
 * 送出方式沿用原本 auth-share.js 的 submitForm：
 *   POST JSON、credentials: 'include'，
 *   回應 { success, message }，success 不為 true 時把 message 當錯誤訊息
 * config.auth.mode 為 'mock' 時不呼叫後端，方便純前端展示
 * ========================================================= */
import config from '../config.js';

const auth = () => config.auth || {};
const endpoint = (name) => auth().endpoints?.[name];
const isMock = () => auth().mode === 'mock';
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * 送出表單資料
 * @returns {Promise<object>} 後端回應
 * @throws {Error} message 可直接顯示給使用者
 */
async function submit(name, data) {
  let res;
  try {
    res = await fetch(endpoint(name), {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  } catch {
    throw new Error('無法連線到伺服器，請確認網路後再試一次。');
  }
  const result = await res.json().catch(() => ({}));
  if (!res.ok || !result.success) {
    throw new Error(result.message || `發生錯誤（伺服器回應 ${res.status}），請再試一次。`);
  }
  return result;
}

const toUser = (u, fallbackName) => (
  typeof u === 'string' ? { name: u, email: '' }
    : { name: u?.username || u?.name || fallbackName || '使用者', email: u?.email || '' }
);

/**
 * 向後端詢問目前登入的使用者（依 session cookie 判斷）
 * @returns {Promise<{ name: string, email: string } | null>} 未登入或無法連線時為 null
 */
export async function fetchCurrentUser() {
  if (isMock()) return null;
  try {
    const res = await fetch(endpoint('me'), {
      credentials: 'include',
      headers: { Accept: 'application/json' },
      cache: 'no-store'
    });
    if (res.status === 401 || !res.ok) return null;
    const result = await res.json();
    return result?.user ? toUser(result.user) : null;
  } catch {
    return null;
  }
}

/** @param {{'login-username': string, 'login-password': string}} data */
export async function login(data) {
  if (isMock()) { await wait(500); return toUser(null, data['login-username']); }
  const result = await submit('login', data);
  return toUser(result.user, data['login-username']);
}

export async function register(data) {
  if (isMock()) { await wait(500); return '註冊成功，請登入。'; }
  return (await submit('register', data)).message || '註冊成功，請登入。';
}

/** 忘記密碼：寄出重設密碼信 */
export async function requestReset(data) {
  if (isMock()) { await wait(600); return '重設密碼的信已寄出。'; }
  return (await submit('forgot', data)).message;
}

/** 從信中連結進來後，設定新密碼 */
export async function renewPassword(data) {
  if (isMock()) { await wait(500); return '密碼已更新，請用新密碼登入。'; }
  return (await submit('reset', data)).message || '密碼已更新，請用新密碼登入。';
}

export async function logout() {
  if (isMock()) return;
  await submit('logout', {});
}
