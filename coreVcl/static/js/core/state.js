/* =========================================================
 * core/state.js — 全域狀態
 * ---------------------------------------------------------
 * 目前選到的主題 / 選單、對話紀錄、登入使用者等。
 * 修改選單請呼叫 navigate()，它會發出 'navigate' 事件。
 * ========================================================= */
import config from '../config.js';
import { emit } from './events.js';

export const state = {
  themeId: config.themes[0]?.id ?? null,
  navId: config.themes[0]?.nav?.[0]?.id ?? null,
  histories: {},   // key: `${themeId}/${navId}` → [{ role, content, time, error? }]
  busy: false,     // AI 回覆中
  user: null       // { name, email }
};

export const getTheme = () => config.themes.find((t) => t.id === state.themeId);
export const getNav = () => getTheme()?.nav?.find((n) => n.id === state.navId);

/** 目前畫面的識別字串，也用來當對話紀錄的 key */
export const currentKey = () => `${state.themeId}/${state.navId}`;

/** 目前選單的對話紀錄（沒有時自動建立） */
export const currentHistory = () => (state.histories[currentKey()] ??= []);

/**
 * 切換主題或選單。只給 themeId 時自動選該主題的第一個選單。
 * @param {{ themeId?: string, navId?: string }} target
 */
export function navigate({ themeId = state.themeId, navId } = {}) {
  const theme = config.themes.find((t) => t.id === themeId);
  if (!theme) return;
  const nextNav = navId ?? (themeId === state.themeId ? state.navId : theme.nav?.[0]?.id ?? null);
  if (themeId === state.themeId && nextNav === state.navId) return;
  state.themeId = themeId;
  state.navId = nextNav;
  emit('navigate', { themeId, navId: nextNav });
}
