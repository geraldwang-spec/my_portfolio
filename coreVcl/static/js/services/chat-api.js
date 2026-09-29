/* =========================================================
 * services/chat-api.js — 向 LLM 取得回覆
 * ---------------------------------------------------------
 * config.api.mode:
 *   'mock'   → 從選單的 mockReplies 輪流回覆（不需後端）
 *   'openai' → 以 OpenAI 相容格式 POST 到 config.api.endpoint
 * ========================================================= */
import config from '../config.js';

/**
 * @param {object} nav       選單設定（使用 systemPrompt、mockReplies）
 * @param {Array}  history   對話紀錄 [{ role, content, error? }]
 * @returns {Promise<string>} AI 的回覆文字
 */
export async function requestReply(nav, history) {
  const api = config.api || {};

  if (api.mode === 'openai') {
    const messages = [
      ...(nav.systemPrompt ? [{ role: 'system', content: nav.systemPrompt }] : []),
      ...history.filter((m) => !m.error).map(({ role, content }) => ({ role, content }))
    ];
    const res = await fetch(api.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(api.headers || {}) },
      body: JSON.stringify({ model: api.model, messages })
    });
    if (!res.ok) throw new Error(`伺服器回應 ${res.status}`);
    const data = await res.json();
    return data.choices?.[0]?.message?.content ?? data.reply ?? '(沒有內容)';
  }

  // mock 模式
  const [min, max] = api.mockDelay || [600, 1400];
  await new Promise((r) => setTimeout(r, min + Math.random() * (max - min)));
  const pool = nav.mockReplies?.length ? nav.mockReplies : ['（mock）已收到你的訊息。'];
  const aiCount = history.filter((m) => m.role === 'assistant').length;
  return pool[aiCount % pool.length];
}
