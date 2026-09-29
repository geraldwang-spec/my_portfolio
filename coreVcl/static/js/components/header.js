/* =========================================================
 * components/header.js — 上方位置列與工作階段計時
 * ========================================================= */
import { getTheme, getNav } from '../core/state.js';
import { on } from '../core/events.js';
import { esc, icon } from '../utils/dom.js';
import { duration } from '../utils/format.js';

export function initHeader() {
  const crumbs = document.getElementById('crumbs');
  const uptime = document.getElementById('uptime');

  const renderCrumbs = () => {
    const theme = getTheme(), nav = getNav();
    crumbs.innerHTML = `<span>${esc(theme?.label ?? '')}</span>` +
      (nav ? `<span class="sep">/</span><span class="current">${icon(nav.icon)}${esc(nav.label)}</span>` : '');
  };
  on('navigate', renderCrumbs);
  renderCrumbs();

  const start = Date.now();
  setInterval(() => { uptime.textContent = duration(Math.floor((Date.now() - start) / 1000)); }, 1000);
}
