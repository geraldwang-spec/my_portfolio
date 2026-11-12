/* =========================================================
 * services/production-api.js — 卡控／生產資料 API
 * 所有網址都帶目前的工作區：/production/workspaces/{id}/...
 * ========================================================= */
import { state } from '../core/state.js';

/** 組出帶工作區的網址；沒有工作區（未登入）時直接丟錯 */
function wsUrl(path) {
  if (state.workspaceId == null) throw new Error('請先登入');
  return `/production/workspaces/${encodeURIComponent(state.workspaceId)}${path}`;
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(wsUrl(path), {
      credentials: 'include',            // 帶上 session cookie，後端才知道是誰
      headers: { Accept: 'application/json', ...options.headers },
      ...options
    });
  } catch {
    throw new Error('無法連線到伺服器，請確認網路後再試一次。');
  }
  const result = await res.json().catch(() => ({}));
  if (!res.ok || !result.success) {
    throw new Error(result.message || `發生錯誤（伺服器回應 ${res.status}），請再試一次。`);
  }
  return result.data;
}

export const fetchHome = () => request('/home');
