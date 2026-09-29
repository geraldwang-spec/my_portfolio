/* =========================================================
 * components/chat.js — AI 對話畫面
 * ========================================================= */
import { state, getTheme, getNav, currentKey, currentHistory } from '../core/state.js';
import { requestReply } from '../services/chat-api.js';
import { esc, icon } from '../utils/dom.js';
import { clockTime } from '../utils/format.js';

let el;

export function initChat() {
  const $ = (id) => document.getElementById(id);
  el = {
    view: $('chatView'), messages: $('messages'), composer: $('composer'), input: $('input'),
    sendBtn: $('sendBtn'), title: $('chatTitle'), sub: $('chatSub'), clearBtn: $('clearBtn')
  };

  el.messages.addEventListener('click', (e) => {
    const chip = e.target.closest('[data-suggest]');
    if (chip) send(chip.dataset.suggest);
  });
  el.clearBtn.addEventListener('click', () => {
    state.histories[currentKey()] = [];
    renderChat();
    el.input.focus();
  });
  el.input.addEventListener('input', () => { autoResize(); updateSendState(); });
  el.input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {   // isComposing：避免注音選字時誤送
      e.preventDefault();
      send(el.input.value);
    }
  });
  el.composer.addEventListener('submit', (e) => { e.preventDefault(); send(el.input.value); });
}

/** 依目前選單重畫對話畫面 */
export function renderChat() {
  const nav = getNav();
  if (!nav) {
    el.title.textContent = getTheme()?.label ?? '';
    el.sub.textContent = '此主題尚未設定選單，請在 config.js 中新增 nav 項目。';
    el.messages.innerHTML = '';
    el.input.disabled = el.sendBtn.disabled = true;
    return;
  }
  el.input.disabled = false;
  el.title.textContent = nav.title || nav.label;
  el.sub.textContent = getTheme().description || '';
  el.input.placeholder = nav.placeholder || '輸入訊息…';

  const list = currentHistory();
  el.messages.innerHTML = list.length ? list.map(messageHTML).join('') : `
    <div class="empty">
      <div class="empty-icon">${icon(nav.icon)}</div>
      <h2>${esc(nav.title || nav.label)}</h2>
      <p>${esc(nav.intro || '')}</p>
      <div class="chips">
        ${(nav.suggestions || []).map((s) => `<button class="chip" data-suggest="${esc(s)}">${esc(s)}</button>`).join('')}
      </div>
    </div>`;
  updateSendState();
  scrollBottom();
}

function messageHTML(m) {
  const who = m.role === 'user' ? 'user' : 'ai';
  return `
    <div class="msg ${who} ${m.error ? 'error' : ''}">
      <div class="avatar">${icon(who === 'user' ? 'user' : 'bot')}</div>
      <div class="bubble-wrap">
        <div class="bubble">${esc(m.content)}</div>
        <span class="meta">${who === 'user' ? '你' : 'AI'} · ${m.time}</span>
      </div>
    </div>`;
}

function appendMessage(m) {
  el.messages.querySelector('.empty')?.remove();
  el.messages.insertAdjacentHTML('beforeend', messageHTML(m));
  scrollBottom();
}

function showTyping() {
  el.messages.insertAdjacentHTML('beforeend', `
    <div class="msg ai" data-typing>
      <div class="avatar">${icon('bot')}</div>
      <div class="bubble-wrap"><div class="bubble typing" aria-label="AI 回覆中"><i></i><i></i><i></i></div></div>
    </div>`);
  scrollBottom();
}
const hideTyping = () => el.messages.querySelector('[data-typing]')?.remove();
const scrollBottom = () => requestAnimationFrame(() => { el.messages.scrollTop = el.messages.scrollHeight; });

async function send(text) {
  text = text.trim();
  if (!text || state.busy) return;
  const nav = getNav();
  const key = currentKey();              // 記下送出時的選單，避免切換後寫錯位置
  const list = currentHistory();

  const userMsg = { role: 'user', content: text, time: clockTime() };
  list.push(userMsg);
  appendMessage(userMsg);
  el.input.value = '';
  autoResize();

  state.busy = true;
  updateSendState();
  showTyping();

  let reply;
  try {
    reply = { role: 'assistant', content: await requestReply(nav, list), time: clockTime() };
  } catch (err) {
    reply = {
      role: 'assistant', error: true, time: clockTime(),
      content: `無法取得回覆：${err.message}。請檢查設定中的 API 端點或網路連線。`
    };
  }
  (state.histories[key] ??= []).push(reply);
  state.busy = false;

  if (key === currentKey() && !el.view.hidden) { hideTyping(); appendMessage(reply); }
  updateSendState();
}

function autoResize() {
  el.input.style.height = 'auto';
  el.input.style.height = Math.min(el.input.scrollHeight, 180) + 'px';
}

function updateSendState() {
  el.sendBtn.disabled = state.busy || !el.input.value.trim() || !getNav();
}
