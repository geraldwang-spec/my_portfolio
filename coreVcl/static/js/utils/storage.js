/* =========================================================
 * utils/storage.js — localStorage 包裝
 * 瀏覽器停用儲存空間（例如無痕模式）時不會拋出錯誤
 * ========================================================= */
export function get(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

export function set(key, value) {
  try { localStorage.setItem(key, value); } catch { /* 無法儲存時忽略 */ }
}

export function getJSON(key, fallback = null) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function setJSON(key, value) {
  set(key, JSON.stringify(value));
}
