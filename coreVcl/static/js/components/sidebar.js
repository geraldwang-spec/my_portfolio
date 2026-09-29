/* =========================================================
 * components/sidebar.js — 左側主題與子選單、收合、手機版抽屜
 * ========================================================= */
import config from '../config.js';
import { state, navigate } from '../core/state.js';
import { on } from '../core/events.js';
import { esc, icon } from '../utils/dom.js';
import * as storage from '../utils/storage.js';

const COLLAPSE_KEY = 'nc-sidebar-collapsed';
let el;

export function initSidebar() {
  el = {
    app: document.getElementById('app'),
    themeList: document.getElementById('themeList'),
    collapseBtn: document.getElementById('collapseBtn'),
    menuBtn: document.getElementById('menuBtn'),
    backdrop: document.getElementById('backdrop'),
    brandName: document.getElementById('brandName'),
    brandTagline: document.getElementById('brandTagline'),
    apiMode: document.getElementById('apiMode')
  };

  el.brandName.textContent = config.app?.name || 'NEON CARBON';
  el.brandTagline.textContent = config.app?.tagline || '';

  el.themeList.addEventListener('click', onListClick);
  el.collapseBtn.addEventListener('click', () => setCollapsed(!el.app.classList.contains('collapsed')));
  el.menuBtn.addEventListener('click', openMobileMenu);
  el.backdrop.addEventListener('click', closeMobileMenu);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !document.querySelector('dialog[open]')) closeMobileMenu();
  });

  on('navigate', render);
  on('api-changed', renderApiMode);

  setCollapsed(storage.get(COLLAPSE_KEY) === '1');
  renderApiMode();
  render();
}

function render() {
  el.themeList.innerHTML = config.themes.map((t) => {
    const active = t.id === state.themeId;
    const subs = active && t.nav?.length ? `
      <div class="sub-list" role="group" aria-label="${esc(t.label)} 功能">
        ${t.nav.map((n) => `
          <button class="sub-item ${n.id === state.navId ? 'active' : ''}"
                  data-nav="${esc(n.id)}" data-tip="${esc(n.label)}"
                  aria-current="${n.id === state.navId ? 'page' : 'false'}">
            ${icon(n.icon)}<span class="label">${esc(n.label)}</span>
          </button>`).join('')}
      </div>` : '';
    return `
      <div class="theme-group">
        <button class="theme-item ${active ? 'active' : ''}"
                data-theme="${esc(t.id)}" data-tip="${esc(t.label)}"
                title="${esc(t.description || t.label)}"
                aria-expanded="${active}">
          ${icon(t.icon)}<span class="label">${esc(t.label)}</span>
          ${t.nav?.length ? icon('chevron', 'caret') : ''}
        </button>
        ${subs}
      </div>`;
  }).join('');
}

function onListClick(e) {
  const sub = e.target.closest('[data-nav]');
  if (sub) {
    navigate({ navId: sub.dataset.nav });
    closeMobileMenu();
    return;
  }
  const theme = e.target.closest('[data-theme]');
  if (theme) navigate({ themeId: theme.dataset.theme });   // 手機版不關抽屜，方便接著選子選單
}

function renderApiMode() {
  el.apiMode.textContent = (config.api?.mode || 'mock').toUpperCase() + ' MODE';
}

function setCollapsed(collapsed) {
  el.app.classList.toggle('collapsed', collapsed);
  const text = collapsed ? '展開側邊欄' : '收合側邊欄';
  el.collapseBtn.setAttribute('aria-expanded', String(!collapsed));
  el.collapseBtn.setAttribute('aria-label', text);
  el.collapseBtn.title = text;
  storage.set(COLLAPSE_KEY, collapsed ? '1' : '0');
}

export function openMobileMenu() {
  el.app.classList.add('mobile-open');
  document.body.classList.add('menu-open');
}

export function closeMobileMenu() {
  el?.app.classList.remove('mobile-open');
  document.body.classList.remove('menu-open');
}
