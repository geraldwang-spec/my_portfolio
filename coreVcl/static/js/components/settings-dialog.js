/* =========================================================
 * components/settings-dialog.js — 設定視窗
 * ---------------------------------------------------------
 * 使用者儲存的 API 設定會覆蓋 config.api，並記在 localStorage
 * ========================================================= */
import config from '../config.js';
import { state } from '../core/state.js';
import { emit } from '../core/events.js';
import * as storage from '../utils/storage.js';
import { closeMobileMenu } from './sidebar.js';

const API_KEY = 'nc-api';

/** 讀回上次儲存的 API 設定（需在其他元件初始化前呼叫） */
export function loadSavedSettings() {
  config.api = { ...(config.api || {}), ...storage.getJSON(API_KEY, {}) };
}

export function initSettings() {
  const btn = document.getElementById('settingsBtn');
  const dlg = document.getElementById('settingsDlg');
  const form = document.getElementById('settingsForm');
  const clearAll = document.getElementById('clearAllBtn');

  btn.addEventListener('click', () => {
    const f = form.elements;
    f.mode.value = config.api.mode || 'mock';
    f.endpoint.value = config.api.endpoint || '';
    f.model.value = config.api.model || '';
    dlg.returnValue = '';
    dlg.showModal();
    closeMobileMenu();
  });

  dlg.addEventListener('close', () => {
    if (dlg.returnValue !== 'save') return;
    const f = form.elements;
    const saved = { mode: f.mode.value, endpoint: f.endpoint.value.trim(), model: f.model.value.trim() };
    Object.assign(config.api, saved);
    storage.setJSON(API_KEY, saved);
    emit('api-changed', saved);
  });

  clearAll.addEventListener('click', () => {
    if (!confirm('確定要清除所有對話嗎？此動作無法復原。')) return;
    state.histories = {};
    emit('history-cleared');
    clearAll.textContent = '已清除';
    setTimeout(() => { clearAll.textContent = '清除所有對話'; }, 1500);
  });
}
