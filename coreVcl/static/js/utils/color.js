/* =========================================================
 * utils/color.js — 色彩換算（純函式，不碰 DOM）
 * ---------------------------------------------------------
 * sRGB（D65）⇄ CIE 1931 XYZ ⇄ xy、相關色溫、白平衡增益
 * ========================================================= */
import { clamp } from './math.js';

/* ---------- sRGB 轉換曲線 ---------- */

/** 8-bit sRGB（0–255）→ 線性值（0–1） */
export const toLinear = (c) => {
  c /= 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
};

/** 線性值 → sRGB 編碼值（0–1，未裁切） */
export const encodeSRGB = (v) => (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055);

/** 線性值 → 8-bit sRGB（0–255） */
export const toSRGB8 = (v) => Math.round(255 * clamp(encodeSRGB(v), 0, 1));

/* ---------- RGB ⇄ XYZ ---------- */

/** 線性 sRGB → XYZ（D65） */
export function linearToXYZ(R, G, B) {
  return [
    0.4124 * R + 0.3576 * G + 0.1805 * B,
    0.2126 * R + 0.7152 * G + 0.0722 * B,
    0.0193 * R + 0.1192 * G + 0.9505 * B
  ];
}

/** 8-bit sRGB → XYZ */
export const rgbToXYZ = (r, g, b) => linearToXYZ(toLinear(r), toLinear(g), toLinear(b));

/** XYZ → 線性 sRGB（未裁切，可能超出 0–1） */
export function xyzToLinear(X, Y, Z) {
  return [
    3.2406 * X - 1.5372 * Y - 0.4986 * Z,
    -0.9689 * X + 1.8758 * Y + 0.0415 * Z,
    0.0557 * X - 0.2040 * Y + 1.0570 * Z
  ];
}

/** XYZ → sRGB 編碼值（0–1，未裁切） */
export const xyzToRgbUnit = (X, Y, Z) => xyzToLinear(X, Y, Z).map(encodeSRGB);

/** XYZ → xy 色度座標；全黑時回傳 null */
export function xyzToXy(X, Y, Z) {
  const s = X + Y + Z;
  return s > 1e-6 ? [X / s, Y / s] : null;
}

/** xy 色度座標 → 用來顯示的 CSS 顏色（亮度正規化到最亮） */
export function xyToDisplayColor(x, y) {
  const [r, g, b] = xyzToRgbUnit(x / y, 1, (1 - x - y) / y).map((v) => Math.max(0, v));
  const m = Math.max(r, g, b, 0.001);
  return `rgb(${Math.round((r / m) * 255)},${Math.round((g / m) * 255)},${Math.round((b / m) * 255)})`;
}

export const toHex = (r, g, b) =>
  '#' + [r, g, b].map((v) => v.toString(16).padStart(2, '0')).join('').toUpperCase();

/* ---------- 相關色溫 ---------- */

/** McCamy 近似公式 */
export function cctMcCamy(x, y) {
  const n = (x - 0.3320) / (0.1858 - y);
  return 449 * n ** 3 + 3525 * n ** 2 + 6823.3 * n + 5520.33;
}

/**
 * 相關色溫只對接近黑體軌跡的顏色有意義：
 * 以 Krystek 近似計算 Duv，|Duv| > 0.05 時回傳 null
 * @returns {{T:number, duv:number} | null}
 */
export function cctWithDuv(x, y) {
  const T = cctMcCamy(x, y);
  if (!(T > 1000 && T < 15000)) return null;
  const d = -2 * x + 12 * y + 3, u = (4 * x) / d, v = (6 * y) / d;
  const uT = (0.860117757 + 1.54118254e-4 * T + 1.28641212e-7 * T * T) / (1 + 8.42420235e-4 * T + 7.08145163e-7 * T * T);
  const vT = (0.317398726 + 4.22806245e-5 * T + 4.20481691e-8 * T * T) / (1 - 2.89741816e-5 * T + 1.61456053e-7 * T * T);
  const duv = Math.hypot(u - uT, v - vT);
  return duv <= 0.05 ? { T, duv } : null;
}

/* ---------- 白平衡 ---------- */

/** 黑體（普朗克）光源在 T K 下的 xy 座標：Kang et al. 2002，適用 1667–25000 K */
export function planckianXy(T) {
  const t = clamp(T, 1667, 25000);
  const x = t <= 4000
    ? -0.2661239e9 / t ** 3 - 0.2343589e6 / t ** 2 + 0.8776956e3 / t + 0.179910
    : -3.0258469e9 / t ** 3 + 2.1070379e6 / t ** 2 + 0.2226347e3 / t + 0.240390;
  const y = t <= 2222 ? -1.1063814 * x ** 3 - 1.34811020 * x ** 2 + 2.18555832 * x - 0.20219683
    : t <= 4000 ? -0.9549476 * x ** 3 - 1.37418593 * x ** 2 + 2.09137015 * x - 0.16748867
      : 3.0817580 * x ** 3 - 5.87338670 * x ** 2 + 3.75112997 * x - 0.37001483;
  return [x, y];
}

/** 色溫 T 的白點換成線性 sRGB（Y = 1） */
function whiteLinear(T) {
  const [x, y] = planckianXy(T);
  return xyzToLinear(x / y, 1, (1 - x - y) / y);
}

const REF = whiteLinear(6504);   // 以 6504 K 為基準，讓 6500 K ≈ 不校正

/**
 * 軟體白平衡增益：把色溫 T 的光源校正為中性白。
 * 在線性 RGB 各通道乘上增益（G 固定為 1）。
 * @param {number} T     光源色溫（K）
 * @param {number} tint  色調，負值偏綠、正值偏洋紅
 * @returns {[number, number, number]} [R, G, B] 增益
 */
export function wbGains(T, tint = 0) {
  const [r, g, b] = whiteLinear(T);
  const [wr, wg, wb] = REF;
  return [(g / r) * (wr / wg), 1 - tint / 200, (g / b) * (wb / wg)];
}
