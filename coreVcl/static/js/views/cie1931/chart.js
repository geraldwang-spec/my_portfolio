/* =========================================================
 * views/cie1931/chart.js — CIE 1931 色度圖（canvas）
 * ---------------------------------------------------------
 * 兩層 canvas：
 *   base    靜態內容（色彩區域、軌跡、刻度、色域、白點），尺寸或色域改變時才重畫
 *   overlay 動態內容（取樣點、軌跡、標記點），每一幀重畫
 * ========================================================= */
import { LOCUS, RANGE, WL_LABELS } from './cmf-data.js';
import { xyzToRgbUnit } from '../../utils/color.js';

const PAD = { l: 44, r: 14, t: 14, b: 34 };
const MONO = "11px 'JetBrains Mono', ui-monospace, monospace";

/* 色度圖底色：只算一次，之後縮放貼上並用光譜軌跡裁切 */
let fieldCache = null;
function colorField() {
  if (fieldCache) return fieldCache;
  const N = 260;
  const c = document.createElement('canvas');
  c.width = c.height = N;
  const g = c.getContext('2d');
  const img = g.createImageData(N, N);
  for (let j = 0; j < N; j++) {
    const y = (1 - (j + 0.5) / N) * RANGE;
    for (let i = 0; i < N; i++) {
      const x = ((i + 0.5) / N) * RANGE;
      const k = (j * N + i) * 4;
      if (y < 0.002 || 1 - x - y < 0) continue;
      let [r, gg, b] = xyzToRgbUnit(x / y, 1, (1 - x - y) / y);
      r = Math.max(0, r); gg = Math.max(0, gg); b = Math.max(0, b);
      const m = Math.max(r, gg, b, 0.001);
      img.data[k] = (r / m) * 255;
      img.data[k + 1] = (gg / m) * 255;
      img.data[k + 2] = (b / m) * 255;
      img.data[k + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  return (fieldCache = c);
}

/**
 * @param {object}   R        畫面元素（chartBox, base, overlay, legend）
 * @param {object}   opt      參數（whitePoint）
 * @param {Array}    gamuts   色域設定，on 表示是否顯示
 * @param {Function} getData  回傳 { sample, trail, points, showTrail }
 */
export function createChart(R, opt, gamuts, getData) {
  const bctx = R.base.getContext('2d');
  const octx = R.overlay.getContext('2d');
  const size = { W: 0, H: 0 };
  const px = (x) => PAD.l + (x / RANGE) * (size.W - PAD.l - PAD.r);
  const py = (y) => size.H - PAD.b - (y / RANGE) * (size.H - PAD.t - PAD.b);
  const css = getComputedStyle(document.documentElement);
  const C = {
    cyan: css.getPropertyValue('--cyan').trim() || '#00e5ff',
    muted: css.getPropertyValue('--muted').trim() || '#71838f',
    text: css.getPropertyValue('--text').trim() || '#d7e3ea'
  };

  function sizeCanvases() {
    const w = R.chartBox.clientWidth, h = R.chartBox.clientHeight;
    if (!w || !h) return false;
    const dpr = window.devicePixelRatio || 1;
    for (const c of [R.base, R.overlay]) {
      c.width = Math.round(w * dpr); c.height = Math.round(h * dpr);
      c.getContext('2d').setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    size.W = w; size.H = h;
    return true;
  }

  function locusPath(g) {
    g.beginPath();
    LOCUS.forEach((p, i) => (i ? g.lineTo(px(p.x), py(p.y)) : g.moveTo(px(p.x), py(p.y))));
    g.closePath();
  }

  function drawBase() {
    const g = bctx, { W, H } = size;
    g.clearRect(0, 0, W, H);

    // 格線
    g.lineWidth = 1;
    for (let i = 0; i <= 8; i++) {
      const v = i / 10;
      g.strokeStyle = 'rgba(0,229,255,0.07)';
      g.beginPath(); g.moveTo(px(v), PAD.t); g.lineTo(px(v), H - PAD.b); g.stroke();
      g.beginPath(); g.moveTo(PAD.l, py(v)); g.lineTo(W - PAD.r, py(v)); g.stroke();
    }
    g.strokeStyle = 'rgba(113,131,143,0.6)';
    g.beginPath(); g.moveTo(PAD.l, PAD.t); g.lineTo(PAD.l, H - PAD.b); g.lineTo(W - PAD.r, H - PAD.b); g.stroke();

    // 色彩區域
    g.save();
    locusPath(g); g.clip();
    g.globalAlpha = 0.9;
    g.imageSmoothingEnabled = true;
    g.drawImage(colorField(), PAD.l, PAD.t, W - PAD.l - PAD.r, H - PAD.t - PAD.b);
    g.restore();

    // 光譜軌跡
    locusPath(g);
    g.strokeStyle = 'rgba(215,227,234,0.85)'; g.lineWidth = 1.5; g.stroke();

    // 刻度
    g.font = MONO; g.fillStyle = C.muted;
    for (let i = 0; i <= 8; i++) {
      const v = i / 10;
      g.textAlign = 'center'; g.textBaseline = 'top'; g.fillText(v.toFixed(1), px(v), H - PAD.b + 7);
      g.textAlign = 'right'; g.textBaseline = 'middle'; g.fillText(v.toFixed(1), PAD.l - 7, py(v));
    }
    g.fillStyle = C.text; g.font = "600 13px 'Chakra Petch', sans-serif";
    g.textAlign = 'right'; g.textBaseline = 'bottom'; g.fillText('x', W - PAD.r, H - 4);
    g.textAlign = 'left'; g.textBaseline = 'top'; g.fillText('y', 6, PAD.t - 2);

    // 波長標籤
    g.font = "10px 'JetBrains Mono', monospace";
    for (const wl of WL_LABELS) {
      const p = LOCUS.find((q) => q.wl === wl); if (!p) continue;
      const dx = p.x - 0.333, dy = p.y - 0.333, len = Math.hypot(dx, dy) || 1;
      g.beginPath(); g.arc(px(p.x), py(p.y), 2, 0, Math.PI * 2);
      g.fillStyle = 'rgba(255,255,255,0.85)'; g.fill();
      g.fillStyle = 'rgba(215,227,234,0.8)'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.fillText(wl, px(p.x) + (dx / len) * 16, py(p.y) - (dy / len) * 16);
    }

    // 色域三角形
    gamuts.filter((gm) => gm.on).forEach((gm) => {
      g.beginPath();
      gm.points.forEach(([x, y], i) => (i ? g.lineTo(px(x), py(y)) : g.moveTo(px(x), py(y))));
      g.closePath();
      g.strokeStyle = gm.color; g.lineWidth = 1.5; g.setLineDash(gm.dash || []); g.stroke(); g.setLineDash([]);
      const [rx, ry] = gm.points[0];
      g.fillStyle = gm.color; g.font = "600 11px 'Chakra Petch', sans-serif";
      g.textAlign = 'right'; g.textBaseline = 'top';
      g.fillText(gm.label, px(rx) - 10, py(ry) + 4);
    });

    // 白點
    const wp = opt.whitePoint;
    if (wp) {
      g.beginPath(); g.arc(px(wp.x), py(wp.y), 4, 0, Math.PI * 2);
      g.fillStyle = '#fff'; g.fill(); g.strokeStyle = '#000'; g.lineWidth = 1; g.stroke();
      g.fillStyle = '#fff'; g.font = "600 11px 'Chakra Petch', sans-serif";
      g.textAlign = 'left'; g.textBaseline = 'top'; g.fillText(wp.label, px(wp.x) + 7, py(wp.y) + 3);
    }
  }

  function drawOverlay() {
    const g = octx, { W, H } = size;
    const { sample: s, trail, points, showTrail } = getData();
    g.clearRect(0, 0, W, H);

    // 取樣軌跡
    if (showTrail && trail.length > 1) {
      trail.forEach((p, i) => {
        const a = (i + 1) / trail.length;
        g.beginPath(); g.arc(px(p.x), py(p.y), 2.2, 0, Math.PI * 2);
        g.fillStyle = `rgba(0,229,255,${0.15 + a * 0.5})`; g.fill();
      });
    }

    // 已標記的點
    points.forEach((p) => {
      const X = px(p.x), Y = py(p.y);
      g.beginPath(); g.arc(X, Y, 6, 0, Math.PI * 2);
      g.fillStyle = p.color; g.fill();
      g.strokeStyle = '#fff'; g.lineWidth = 1.5; g.stroke();
      g.fillStyle = '#fff'; g.font = "600 11px 'Chakra Petch', sans-serif";
      g.textAlign = 'left'; g.textBaseline = 'bottom';
      g.shadowColor = 'rgba(0,0,0,.8)'; g.shadowBlur = 3;
      g.fillText(p.label, X + 9, Y - 4);
      g.shadowBlur = 0;
    });

    // 目前取樣點
    if (s && s.x != null) {
      const X = px(s.x), Y = py(s.y);
      g.strokeStyle = 'rgba(0,229,255,0.45)'; g.lineWidth = 1; g.setLineDash([4, 4]);
      g.beginPath(); g.moveTo(PAD.l, Y); g.lineTo(X - 10, Y); g.moveTo(X + 10, Y); g.lineTo(W - PAD.r, Y);
      g.moveTo(X, PAD.t); g.lineTo(X, Y - 10); g.moveTo(X, Y + 10); g.lineTo(X, H - PAD.b); g.stroke();
      g.setLineDash([]);
      g.shadowColor = C.cyan; g.shadowBlur = 12;
      g.beginPath(); g.arc(X, Y, 7, 0, Math.PI * 2);
      g.strokeStyle = C.cyan; g.lineWidth = 2; g.stroke();
      g.shadowBlur = 0;
      g.beginPath(); g.arc(X, Y, 4, 0, Math.PI * 2);
      g.fillStyle = `rgb(${s.r},${s.g},${s.b})`; g.fill();
    }
  }

  function redraw() {
    if (sizeCanvases()) { drawBase(); drawOverlay(); }
  }

  let resizeTimer;
  const ro = new ResizeObserver(() => { clearTimeout(resizeTimer); resizeTimer = setTimeout(redraw, 60); });
  ro.observe(R.chartBox);

  R.legend.addEventListener('change', (e) => {
    const i = e.target.dataset.gamut;
    if (i != null) { gamuts[i].on = e.target.checked; drawBase(); }
    drawOverlay();
  });

  requestAnimationFrame(redraw);
  document.fonts?.ready.then(redraw);   // 字型載入後刻度文字才會正確

  return {
    drawOverlay,
    redraw,
    destroy() { ro.disconnect(); clearTimeout(resizeTimer); }
  };
}
