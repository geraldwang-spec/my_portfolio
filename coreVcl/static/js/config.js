/* =========================================================
 * config.js — 主題 / 選單設定檔（ES module）
 * ---------------------------------------------------------
 * 擴充方式：
 *  1. 新增主題：在 themes 陣列中加入一個物件（id 不可重複）
 *  2. 新增功能選單：在該主題的 nav 陣列中加入項目（顯示於 sidebar 主題下方）
 *  3. 圖示：在 icons 中新增 SVG path，再用 icon: '名稱' 引用
 *  4. 串接真實 API：把 api.mode 改成 'openai'，填入 endpoint / model
 *  5. 登入 / 註冊 / 忘記密碼：在主畫面的登入視窗完成，後端路由見 auth.endpoints
 *  6. 畫面類型：nav 項目預設為 AI 對話；設定 type（例如 'cie1931'）即改用
 *     js/views/ 下對應的畫面模組（在 js/views/index.js 註冊）
 * ========================================================= */

const config = {
  app: {
    name: 'NEON CARBON',
    tagline: 'AI Console',
    version: 'v1.0.0'
  },

  /* ---------- API 設定 ----------
   * mode: 'mock'   → 使用下方各選單的 mockReplies 模擬回覆（不需後端）
   * mode: 'openai' → 以 OpenAI 相容格式 POST 到 endpoint
   *                  （建議指向自己的後端代理，不要把金鑰放在前端）
   */
  api: {
    mode: 'mock',
    endpoint: '/api/chat',
    model: 'gpt-4o-mini',
    headers: {},
    mockDelay: [600, 1400] // 模擬回覆延遲（毫秒，最小～最大）
  },

  /* ---------- 登入設定 ----------
   * mode: 'server' → 呼叫下方 endpoints（Flask /auth/*），頁面載入時以 me 取得目前使用者
   * mode: 'mock'   → 純前端示範，不需後端
   *
   * 各路由收到的欄位（JSON）：
   *   login     { login-username, login-password }
   *   register  { register-username, register-password, register-repeat, register-email }
   *   forgot    { reset-username, reset-email }        → 寄出重設密碼信
   *   reset     { reset-pw-password, reset-pw-repeat } → 設定新密碼（token 由後端 session 保存）
   *   logout    {}
   *   me        GET，回傳 { success: true, user: { username, email } | null }（未登入也可回 401）
   * 回應格式：{ success: true|false, message: '...' }，login 成功時可另外回傳 user: { username, email }
   *
   * 信中的重設連結：後端驗證 token 後導向 /?auth=reset（失效時 /?auth=reset-invalid），
   * 主畫面會自動打開登入視窗的對應畫面。
   */
  auth: {
    mode: 'server',
    passwordMinLength: 6,
    resendCooldown: 60,            // 重新寄送重設信的等待秒數
    endpoints: {
      login: '/auth/login',
      register: '/auth/register',
      forgot: '/auth/resetpasswd',
      reset: '/auth/renew_password',
      logout: '/auth/logout',
      me: '/auth/me'
    }
  },

  /* ---------- 主題（顯示在左側 sidebar） ---------- */
  themes: [
    {
      id: 'llm-api',
      label: 'LLM API',
      icon: 'cpu',
      description: '透過大型語言模型提供的各項服務',

      /* ---------- 功能選單（顯示在 sidebar 主題下方） ---------- */
      nav: [
        {
          id: 'weather',
          label: '天氣',
          icon: 'cloud',
          title: '天氣助理',
          intro: '詢問任一城市的天氣、未來幾天的預報，或是出門該不該帶傘。',
          placeholder: '例如：台北明天會下雨嗎？',
          systemPrompt: '你是一位天氣助理，使用繁體中文，回答簡潔並提供實用建議。',
          suggestions: [
            '台北今天天氣如何？',
            '這週末適合去陽明山嗎？',
            '明天早上通勤要帶傘嗎？'
          ],
          mockReplies: [
            '台北目前 28°C，多雲，濕度 74%。午後有 40% 機率出現短暫雷陣雨，出門建議帶把折疊傘。',
            '未來三天以晴時多雲為主，高溫約 30～32°C，週末山區午後容易起霧，上山請留意視線與保暖。',
            '明早降雨機率約 20%，通勤時段應該不會下雨，但傍晚有局部陣雨的可能，帶傘比較保險。'
          ]
        },
        {
          id: 'shop',
          label: '商店',
          icon: 'bag',
          title: '購物助理',
          intro: '描述你想買的東西、預算和用途，我會幫你比較並推薦商品。',
          placeholder: '例如：推薦一副 3000 元以內的降噪耳機',
          systemPrompt: '你是一位購物助理，使用繁體中文，依照使用者的預算與需求推薦商品並說明理由。',
          suggestions: [
            '推薦 3000 元以內的降噪耳機',
            '送給同事的生日禮物有什麼好選擇？',
            '幫我比較兩款入門機械鍵盤'
          ],
          mockReplies: [
            '依你的預算，我會先看三個方向：\n1. 主打降噪效果的入耳式耳機\n2. 通勤友善、續航長的款式\n3. 通話品質好的款式\n\n你比較常在哪裡使用？捷運、辦公室還是運動時？',
            '送同事的禮物可以考慮實用又不會太私人的東西，例如手沖咖啡組、質感文具，或是桌面小盆栽。預算大約多少呢？',
            '入門機械鍵盤主要差在軸體手感、配列大小和連線方式。如果你常打字，茶軸或紅軸會比較舒服；想要桌面整潔可以選 75% 配列的藍牙款。'
          ]
        }
      ]
    }

    ,{
      id: 'image-processing',
      label: '影像處理',
      icon: 'image',
      description: '色彩與影像相關的分析工具',
      nav: [
        {
          id: 'cie1931',
          label: 'CIE1931',
          icon: 'cie',
          type: 'cie1931',                 // 畫面類型：對應 js/views/cie1931.js
          title: 'CIE 1931 色度分析',
          intro: '即時擷取攝影機影像，將取樣點顏色換算為 xy 色度座標並標在色度圖上。',
          options: {
            resolution: { width: 1280, height: 720 },
            facingMode: 'environment',     // 手機優先使用後鏡頭
            sampleSize: 9,                 // 取樣框大小（像素）
            trailLength: 40,               // 軌跡點數
            projects: {                    // 標記點專案（存在瀏覽器 localStorage）
              storageKey: 'nc-cie1931-projects',
              defaultName: '預設專案'
            },
            whitePoint: { label: 'D65', x: 0.3127, y: 0.3290 },
            whiteBalance: {
              min: 2000, max: 10000, step: 50,
              value: 6500,                 // 手動時的預設色溫；6500 K 約等於不校正
              tintRange: 50,               // 色調調整範圍 ±50（僅軟體白平衡）
              presets: [
                { label: '鎢絲燈', value: 2850 },
                { label: '螢光燈', value: 4000 },
                { label: '日光', value: 5500 },
                { label: '陰天', value: 6500 }
              ]
            },
            gamuts: [
              { label: 'sRGB', color: '#00e5ff', points: [[0.640, 0.330], [0.300, 0.600], [0.150, 0.060]] },
              { label: 'DCI-P3', color: '#ff4fd8', dash: [5, 4], visible: false, points: [[0.680, 0.320], [0.265, 0.690], [0.150, 0.060]] },
              { label: 'Rec.2020', color: '#ffd23f', dash: [2, 3], visible: false, points: [[0.708, 0.292], [0.170, 0.797], [0.131, 0.046]] }
            ]
          }
        }
      ]
    }

    /* 新增主題範例：複製上方主題物件，修改 id / label / icon / nav 即可 */
  ],

  /* ---------- 圖示庫（24x24 viewBox 的 SVG 內容） ---------- */
  icons: {
    cpu: '<rect x="6" y="6" width="12" height="12" rx="1"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    cloud: '<path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.1 9.3 4.35 4.35 0 0 0 7 18z"/><path d="M9 21l1-2M13 21l1-2"/>',
    bag: '<path d="M5 8h14l-1 13H6L5 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    image: '<rect x="3" y="4" width="18" height="16" rx="1"/><circle cx="9" cy="10" r="2"/><path d="M21 17l-5-5-9 8"/>',
    scan: '<path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4M7 12h10"/>',
    chevron: '<path d="M15 6l-6 6 6 6"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    send: '<path d="M4 12l16-8-6 16-2.5-6.5L4 12z"/>',
    trash: '<path d="M5 7h14M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    bot: '<rect x="4" y="8" width="16" height="11" rx="2"/><path d="M12 4v4M9 13h.01M15 13h.01"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    sidebar: '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M9 4v16M16 10l-2 2 2 2"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    login: '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M3 7l9 6 9-6"/>',
    alert: '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18h.01"/>',
    key: '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3M15 8l2 2"/>',
    back: '<path d="M15 6l-6 6 6 6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    edit: '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M13 7l4 4"/>',
    camera: '<path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8z"/><circle cx="12" cy="13" r="4"/>',
    cie: '<path d="M4 20V4M4 20h16"/><path d="M7 17c-1-4 0-9 3-11 2-1.3 3.5 1 5 4s3 5 1 7H7z"/><circle cx="11" cy="13" r="1"/>'
  }
};

export default config;
