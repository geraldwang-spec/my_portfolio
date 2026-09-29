/* =========================================================
 * views/cie1931/index.js — CIE 1931 畫面進入點
 * ---------------------------------------------------------
 * 參考：geraldwang-spec/my_practise stocks_project
 *   templates/camera.html、templates/cie1931_chromaticity.html
 *
 * 這個檔案只負責「組裝」：產生 HTML，建立各個子模組並把它們接起來。
 *
 *   source.js         影像來源（攝影機 / 示範影像）與取樣
 *   white-balance.js  白平衡（硬體 / 軟體）
 *   chart.js          色度圖
 *   readout.js        取樣結果卡片
 *   projects.js       專案與標記點（資料在 projects-store.js）
 * ========================================================= */
import { loadCSS, collectRefs } from '../../utils/dom.js';
import { mergeOptions } from './defaults.js';
import { template } from './template.js';
import { createSource } from './source.js';
import { createWhiteBalance } from './white-balance.js';
import { createChart } from './chart.js';
import { createProjects } from './projects.js';
import { renderReadout } from './readout.js';

/**
 * @param {HTMLElement} root  要放入畫面的容器
 * @param {object} nav        config.js 的選單設定
 * @returns {Promise<() => void>} unmount：離開畫面時呼叫，會釋放攝影機
 */
export async function mount(root, nav) {
  // 樣式表與這個檔案放在同一個資料夾，用 import.meta.url 算出網址
  await loadCSS('cie1931', () => new URL('./cie1931.css', import.meta.url));

  const opt = mergeOptions(nav.options);
  const gamuts = (opt.gamuts || []).map((g) => ({ ...g, on: g.visible !== false }));
  const filterId = 'wbf-' + Math.random().toString(36).slice(2, 8);

  root.innerHTML = template({ nav, opt, gamuts, filterId });
  const R = collectRefs(root);

  /* 畫面共用的即時資料 */
  const live = { sample: null, trail: [], lastTrail: 0, lastReadout: 0 };
  const clearTrail = () => { live.trail = []; };

  let projects;   // 先宣告，chart 讀取點位時才會用到
  const chart = createChart(R, opt, gamuts, () => ({
    sample: live.sample,
    trail: live.trail,
    points: projects?.points ?? [],
    showTrail: R.trailToggle.checked
  }));

  projects = createProjects(R, opt, {
    getSample: () => live.sample,
    onChange: () => chart.drawOverlay()
  });
  projects.setSampleAvailable(false);

  const wb = createWhiteBalance(R, opt, filterId, { onChange: clearTrail });
  wb.reset('開啟影像來源後即可調整。');

  const source = createSource(R, opt, {
    getGains: () => wb.gains,

    onStart(mode, track) {
      live.sample = null;
      clearTrail();
      projects.setSampleAvailable(true);
      wb.setup(mode, track);
    },

    onStop() {
      live.sample = null;
      clearTrail();
      projects.setSampleAvailable(false);
      wb.reset('開啟影像來源後即可調整。');
      renderReadout(R, null);
      chart.drawOverlay();
    },

    onMove: clearTrail,

    onFrame(sample, t) {
      live.sample = sample;
      if (sample.x != null && t - live.lastTrail > 90) {
        live.trail.push({ x: sample.x, y: sample.y });
        if (live.trail.length > opt.trailLength) live.trail.shift();
        live.lastTrail = t;
      }
      if (t - live.lastReadout > 100) {       // 文字每 0.1 秒更新一次就夠了
        renderReadout(R, sample);
        live.lastReadout = t;
      }
      chart.drawOverlay();
    }
  });

  renderReadout(R, null);

  return function unmount() {
    source.destroy();
    chart.destroy();
    wb.destroy();
    root.innerHTML = '';
  };
}
