/* =========================================================
 * main.js — 程式進入點
 * ---------------------------------------------------------
 * index.html 只載入這一支：<script type="module" src=".../main.js">
 * 其他檔案都經由 import 自動載入。
 * ========================================================= */
import config from './config.js';
import { hydrateIcons } from './utils/dom.js';
import { initSidebar } from './components/sidebar.js';
import { initHeader } from './components/header.js';
import { initChat } from './components/chat.js';
import { initMainView } from './components/main-view.js';
import { initSettings, loadSavedSettings } from './components/settings-dialog.js';
import { initAccount } from './components/account.js';
import { initAuthDialog } from './components/auth-dialog.js';

if (!Array.isArray(config.themes) || !config.themes.length) {
  document.body.innerHTML = '<p style="padding:24px;color:#ff5470">config.js 的 themes 是空的，請至少設定一個主題。</p>';
} else {
  loadSavedSettings();      // 先套用使用者儲存的 API 設定
  hydrateIcons();           // HTML 裡的 <i data-icon> → SVG
  initSidebar();
  initHeader();
  initSettings();
  initAuthDialog();         // 需在 initAccount 之前（網址帶 ?auth= 時會自動開啟）
  initAccount();
  initChat();
  initMainView();           // 最後初始化，第一次畫出主畫面
}
