/* =========================================================
 * views/cie1931/white-balance.js — 白平衡
 * ---------------------------------------------------------
 * 攝影機支援時 → 以 MediaStreamTrack constraints 調整硬體（同原本 camera.js）
 * 不支援或示範影像 → 軟體白平衡：畫面套 SVG 色彩矩陣，取樣值同步乘上增益
 * ========================================================= */
import { clamp } from '../../utils/math.js';
import { wbGains } from '../../utils/color.js';

/**
 * @param {object} R          畫面元素
 * @param {object} opt        參數（whiteBalance）
 * @param {string} filterId   SVG 濾鏡 id
 * @param {object} hooks
 * @param {() => void} hooks.onChange  白平衡改變（用來清除色度圖軌跡）
 */
export function createWhiteBalance(R, opt, filterId, hooks) {
  const WB = opt.whiteBalance;
  const S = { mode: null, track: null, hw: false, gains: null };
  let timer;

  /* ---------- 軟體增益 ---------- */
  function setGains(g) {
    S.gains = g;
    const [r, gg, b] = g || [1, 1, 1];
    R.wbMatrix.setAttribute('values', `${r} 0 0 0 0  0 ${gg} 0 0 0  0 0 ${b} 0 0  0 0 0 1 0`);
    const f = g ? `url(#${filterId})` : '';
    R.video.style.filter = f;
    R.demo.style.filter = f;
    R.wbGains.hidden = !g;
    if (g) R.wbGains.textContent = `增益  R ×${r.toFixed(2)}  G ×${gg.toFixed(2)}  B ×${b.toFixed(2)}`;
    hooks.onChange();
  }

  /* ---------- 狀態切換 ---------- */
  function reset(note) {
    S.mode = S.track = null;
    setGains(null);
    R.wbSwitch.checked = false;
    R.wbSwitch.disabled = true;
    R.wbManual.hidden = R.wbReset.hidden = true;
    R.wbNote.textContent = note;
  }

  /** 影像開始播放時呼叫，判斷要用硬體或軟體白平衡 */
  function setup(mode, track) {
    S.mode = mode;
    S.track = track;
    const caps = mode === 'camera' ? (track?.getCapabilities?.() || {}) : {};
    S.hw = (caps.whiteBalanceMode || []).includes('manual') && !!caps.colorTemperature;

    if (S.hw) {
      const ct = caps.colorTemperature;
      setSliderRange(ct.min, ct.max, ct.step || 50);
      R.wbSlider.value = track.getSettings().colorTemperature || clamp(WB.value, ct.min, ct.max);
    } else {
      setSliderRange(WB.min, WB.max, WB.step);
      R.wbSlider.value = WB.value;
    }
    R.wbOut.textContent = R.wbSlider.value;
    R.tintSlider.value = 0;
    R.tintOut.textContent = '0';
    R.tintWrap.hidden = S.hw;                     // 硬體只提供色溫，色調僅軟體模式可用
    R.wbSwitch.disabled = false;
    R.wbSwitch.checked = S.hw && track.getSettings().whiteBalanceMode === 'manual';
    R.wbManual.hidden = R.wbReset.hidden = !R.wbSwitch.checked;
    setGains(null);
    markPreset();
    R.wbNote.textContent = describe();
  }

  function setSliderRange(min, max, step) {
    R.wbSlider.min = min; R.wbSlider.max = max; R.wbSlider.step = step;
    R.wbMinL.textContent = `${min} K`;
    R.wbMaxL.textContent = `${max} K`;
    R.presets.querySelectorAll('[data-preset]').forEach((b) => {
      const v = Number(b.dataset.preset);
      b.disabled = v < min || v > max;
    });
  }

  function markPreset() {
    R.presets.querySelectorAll('[data-preset]').forEach((b) =>
      b.setAttribute('aria-pressed', String(b.dataset.preset === R.wbSlider.value)));
  }

  function describe() {
    const manual = R.wbSwitch.checked, demo = S.mode === 'demo';
    if (S.hw) return manual ? `手動：由攝影機硬體調整為 ${R.wbSlider.value} K。` : '自動：由攝影機硬體自動調整。';
    if (manual) {
      return (demo ? '手動：以軟體校正影像與取樣值。' : '手動：攝影機不支援硬體白平衡，改以軟體校正影像與取樣值。')
        + '把色溫設成現場光源的色溫，白色就會回到中性。';
    }
    return demo ? '自動：示範影像不做校正，切到手動即可調整。'
      : '自動：攝影機不支援硬體白平衡，目前不做校正。切到手動即可用軟體調整。';
  }

  /* ---------- 套用 ---------- */
  async function apply() {
    markPreset();
    const manual = R.wbSwitch.checked;
    R.wbManual.hidden = R.wbReset.hidden = !manual;

    if (!S.hw) {
      setGains(manual ? wbGains(Number(R.wbSlider.value), Number(R.tintSlider.value)) : null);
      R.wbNote.textContent = describe();
      return;
    }
    if (!S.track) return;
    const setting = { whiteBalanceMode: manual ? 'manual' : 'continuous' };
    if (manual) setting.colorTemperature = Number(R.wbSlider.value);
    try {
      await S.track.applyConstraints({ advanced: [setting] });
      hooks.onChange();
      R.wbNote.textContent = describe();
    } catch (err) {
      R.wbNote.textContent = `無法套用白平衡設定：${err.message}`;
    }
  }

  const schedule = () => { clearTimeout(timer); timer = setTimeout(apply, S.hw ? 120 : 16); };

  /* ---------- 事件 ---------- */
  R.wbSwitch.addEventListener('change', apply);
  R.wbSlider.addEventListener('input', () => { R.wbOut.textContent = R.wbSlider.value; schedule(); });
  R.tintSlider.addEventListener('input', () => {
    const v = Number(R.tintSlider.value);
    R.tintOut.textContent = v > 0 ? `+${v}` : String(v);
    schedule();
  });
  R.presets.addEventListener('click', (e) => {
    const b = e.target.closest('[data-preset]');
    if (!b) return;
    R.wbSlider.value = b.dataset.preset;
    R.wbOut.textContent = R.wbSlider.value;
    apply();
  });
  R.wbReset.addEventListener('click', () => {
    R.wbSlider.value = clamp(WB.value, Number(R.wbSlider.min), Number(R.wbSlider.max));
    R.wbOut.textContent = R.wbSlider.value;
    R.tintSlider.value = 0;
    R.tintOut.textContent = '0';
    apply();
  });

  return {
    setup,
    reset,
    /** 軟體白平衡增益；null 表示不校正 */
    get gains() { return S.gains; },
    destroy() { clearTimeout(timer); }
  };
}
