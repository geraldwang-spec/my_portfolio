/* =========================================================
 * views/cie1931/defaults.js — 預設參數
 * ---------------------------------------------------------
 * config.js 裡選單的 options 會覆蓋這些值
 * ========================================================= */
export const DEFAULTS = {
  resolution: { width: 1280, height: 720 },
  facingMode: 'environment',
  sampleSize: 9,            // 取樣框邊長（像素），取平均降低雜訊
  trailLength: 40,          // 色度圖上保留的軌跡點數
  projects: {               // 標記點依專案分組，儲存在瀏覽器（localStorage）
    storageKey: 'nc-cie1931-projects',
    defaultName: '預設專案'
  },
  whitePoint: { label: 'D65', x: 0.3127, y: 0.3290 },
  gamuts: [],
  whiteBalance: {
    min: 2000, max: 10000, step: 50, value: 6500,   // 色溫（K）
    tintRange: 50,                                   // 色調 ±（負值偏綠、正值偏洋紅）
    presets: [
      { label: '鎢絲燈', value: 2850 },
      { label: '螢光燈', value: 4000 },
      { label: '日光', value: 5500 },
      { label: '陰天', value: 6500 }
    ]
  }
};

/** 合併預設值與 config.js 的 options（巢狀物件也會合併） */
export function mergeOptions(options = {}) {
  return {
    ...DEFAULTS,
    ...options,
    projects: { ...DEFAULTS.projects, ...(options.projects || {}) },
    whiteBalance: { ...DEFAULTS.whiteBalance, ...(options.whiteBalance || {}) }
  };
}
