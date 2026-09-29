/* =========================================================
 * views/cie1931/demo-pattern.js — 示範影像
 * ---------------------------------------------------------
 * 沒有攝影機時使用：緩慢移動的 ColorChecker 24 色色塊（sRGB 近似值）
 * ========================================================= */
const PATCHES = [
  '#735244', '#c29682', '#627a9d', '#576c43', '#8580b1', '#67bdaa',
  '#d67e2c', '#505ba6', '#c15a63', '#5e3c6c', '#9dbc40', '#e0a32e',
  '#383d96', '#469449', '#af363c', '#e7c71f', '#bb5695', '#0885a1',
  '#f3f3f2', '#c8c8c8', '#a0a0a0', '#7a7a79', '#555555', '#343434'
];

export const DEMO_WIDTH = 640;
export const DEMO_HEIGHT = 480;

/**
 * 在 canvas 上畫出第 t 毫秒的畫面
 * @param {CanvasRenderingContext2D} g
 * @param {number} t  requestAnimationFrame 的時間戳記
 */
export function drawDemoPattern(g, t) {
  const size = 96, gap = 12, step = size + gap, cols = 6, rows = 4;
  g.fillStyle = '#16191c';
  g.fillRect(0, 0, DEMO_WIDTH, DEMO_HEIGHT);
  const period = cols * step;
  const ox = -((t * 0.035) % period);
  const oy = DEMO_HEIGHT / 2 - size / 2 - 2 * step + Math.sin(t / 1600) * 28;   // 讓中央正好落在第三列
  for (let rep = 0; rep < 3; rep++) {
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        g.fillStyle = PATCHES[r * cols + c];
        g.fillRect(ox + rep * period + c * step, oy + r * step, size, size);
      }
    }
  }
}
