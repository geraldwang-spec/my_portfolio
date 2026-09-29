/* =========================================================
 * utils/dom.js — DOM 相關的小工具
 * ========================================================= */
import config from '../config.js';

/** 跳脫 HTML 特殊字元，所有插入 innerHTML 的使用者資料都要經過它 */
export const esc = (s) => String(s).replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

/** 依名稱產生 config.icons 裡的 SVG 圖示 */
export const icon = (name, cls = '') =>
  `<svg viewBox="0 0 24 24" aria-hidden="true"${cls ? ` class="${cls}"` : ''}>${config.icons?.[name] || ''}</svg>`;

/** 把 HTML 裡的 <i data-icon="名稱"> 換成 SVG */
export function hydrateIcons(root = document) {
  root.querySelectorAll('i[data-icon]').forEach((n) => { n.outerHTML = icon(n.dataset.icon); });
}

/** 收集 root 底下所有 [data-ref] 元素，回傳 { 名稱: 元素 } */
export function collectRefs(root) {
  const refs = {};
  root.querySelectorAll('[data-ref]').forEach((n) => { refs[n.dataset.ref] = n; });
  return refs;
}

/**
 * 動態載入樣式表（同一個 id 只載入一次），載入完成才 resolve，避免畫面閃爍。
 * @param {string} id   識別名稱，頁面上已有 [data-css="id"] 時直接略過
 * @param {string|URL|(() => string|URL)} href  樣式表網址（可傳函式，需要時才計算）
 */
export function loadCSS(id, href) {
  if (document.querySelector(`[data-css="${id}"]`)) return Promise.resolve();
  return new Promise((resolve) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = String(typeof href === 'function' ? href() : href);
    link.dataset.css = id;
    link.onload = link.onerror = () => resolve();
    document.head.appendChild(link);
  });
}
