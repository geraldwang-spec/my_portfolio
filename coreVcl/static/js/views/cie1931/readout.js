/* =========================================================
 * views/cie1931/readout.js — 取樣結果卡片
 * ========================================================= */
import { toHex, cctWithDuv } from '../../utils/color.js';

/**
 * @param {object} R       畫面元素
 * @param {object|null} s  取樣結果（null 表示沒有影像）
 */
export function renderReadout(R, s) {
  if (!s) {
    R.swatch.style.background = '';
    R.vxy.textContent = R.vcct.textContent = R.vrgb.textContent = R.vhex.textContent = R.vxyz.textContent = '—';
    R.vcct.title = '';
    R.dimNote.hidden = true;
    return;
  }
  R.swatch.style.background = `rgb(${s.r},${s.g},${s.b})`;
  R.vrgb.textContent = `${s.r}, ${s.g}, ${s.b}`;
  R.vhex.textContent = toHex(s.r, s.g, s.b);
  R.vxyz.textContent = `${s.X.toFixed(4)}, ${s.Y.toFixed(4)}, ${s.Z.toFixed(4)}`;

  if (s.x == null) {
    R.vxy.textContent = R.vcct.textContent = '—';
  } else {
    R.vxy.textContent = `${s.x.toFixed(4)}, ${s.y.toFixed(4)}`;
    const c = cctWithDuv(s.x, s.y);
    R.vcct.textContent = c ? `${Math.round(c.T)} K` : '不適用';
    R.vcct.title = c ? `Duv ${c.duv.toFixed(4)}` : '此顏色偏離黑體軌跡（|Duv| > 0.05），相關色溫沒有意義';
  }
  R.dimNote.hidden = s.Y >= 0.01;
}
