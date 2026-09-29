/* =========================================================
 * utils/format.js — 格式化
 * ========================================================= */

/** 目前時間 HH:MM */
export const clockTime = () =>
  new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', hour12: false });

/** 秒數 → HH:MM:SS */
export const duration = (sec) =>
  [sec / 3600, (sec % 3600) / 60, sec % 60].map((n) => String(Math.floor(n)).padStart(2, '0')).join(':');
