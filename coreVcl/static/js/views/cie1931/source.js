/* =========================================================
 * views/cie1931/source.js — 影像來源與取樣
 * ---------------------------------------------------------
 * 負責：開啟 / 停止攝影機、示範影像、切換攝影機、
 *       取樣框位置、每一幀讀取取樣區平均顏色並換算 XYZ / xy
 * （攝影機部分參考原本的 camera.js）
 * ========================================================= */
import { esc } from '../../utils/dom.js';
import { clamp } from '../../utils/math.js';
import { toLinear, toSRGB8, linearToXYZ, rgbToXYZ, xyzToXy } from '../../utils/color.js';
import { drawDemoPattern } from './demo-pattern.js';

const CAMERA_ERRORS = {
  NotAllowedError: '攝影機權限被拒絕。請在瀏覽器網址列允許使用攝影機後再試一次，或改用示範影像。',
  NotFoundError: '找不到攝影機。請確認裝置已連接，或改用示範影像。',
  NotReadableError: '攝影機正被其他程式使用中。請關閉其他使用攝影機的程式後再試一次。',
  OverconstrainedError: '這支攝影機不支援目前設定的解析度。請調整 config.js 的 resolution 後再試一次。'
};

/**
 * 把平均 RGB 換算成取樣結果；有白平衡增益時先在線性 RGB 上校正
 * @returns {{ r, g, b, X, Y, Z, x, y }}  x、y 在全黑時為 null
 */
export function measure(r, g, b, gains) {
  let X, Y, Z;
  if (gains) {
    const lr = Math.min(1, toLinear(r) * gains[0]);
    const lg = Math.min(1, toLinear(g) * gains[1]);
    const lb = Math.min(1, toLinear(b) * gains[2]);
    [X, Y, Z] = linearToXYZ(lr, lg, lb);
    r = toSRGB8(lr); g = toSRGB8(lg); b = toSRGB8(lb);
  } else {
    [X, Y, Z] = rgbToXYZ(r, g, b);
  }
  const xy = xyzToXy(X, Y, Z);
  return { r, g, b, X, Y, Z, x: xy?.[0] ?? null, y: xy?.[1] ?? null };
}

/**
 * @param {object} R     畫面元素
 * @param {object} opt   參數（resolution, facingMode, sampleSize）
 * @param {object} hooks
 * @param {() => number[]|null} hooks.getGains      目前的軟體白平衡增益
 * @param {(mode, track) => void} hooks.onStart     開始播放（mode: 'camera' | 'demo'）
 * @param {() => void} hooks.onStop                 停止播放
 * @param {(sample, t) => void} hooks.onFrame       每一幀的取樣結果
 * @param {() => void} hooks.onMove                 取樣位置改變
 */
export function createSource(R, opt, hooks) {
  const S = { stream: null, track: null, el: null, mode: null, u: 0.5, v: 0.5, raf: 0, lastTag: 0 };
  const n = opt.sampleSize;
  const helper = document.createElement('canvas');
  helper.width = helper.height = n;
  const hctx = helper.getContext('2d', { willReadFrequently: true });
  const demoCtx = R.demo.getContext('2d');

  R.video.hidden = true;

  /* ---------- 開始 / 停止 ---------- */
  function showRunning(mode) {
    S.mode = mode;
    R.camEmpty.hidden = true;
    R.reticle.hidden = R.camTag.hidden = R.stop.hidden = false;
    R.video.hidden = mode !== 'camera';
    R.demo.hidden = mode !== 'demo';
    placeReticle();
    if (!S.raf) S.raf = requestAnimationFrame(tick);
    hooks.onStart(mode, S.track);
  }

  function release() {
    cancelAnimationFrame(S.raf); S.raf = 0;
    S.stream?.getTracks().forEach((t) => t.stop());
    S.stream = S.track = S.el = S.mode = null;
    R.video.srcObject = null;
  }

  function stop() {
    release();
    R.camEmpty.hidden = false;
    R.reticle.hidden = R.camTag.hidden = R.stop.hidden = R.device.hidden = true;
    R.video.hidden = R.demo.hidden = true;
    R.camBox.style.aspectRatio = '';
    hooks.onStop();
  }

  async function startCamera(deviceId) {
    R.camError.textContent = '';
    if (!navigator.mediaDevices?.getUserMedia) {
      R.camError.textContent = '這個頁面無法使用攝影機：需要在 HTTPS 或 localhost 環境下開啟。可以先用示範影像查看效果。';
      return;
    }
    R.startCam.disabled = true;
    try {
      const video = {
        width: { ideal: opt.resolution.width },
        height: { ideal: opt.resolution.height },
        ...(deviceId ? { deviceId: { exact: deviceId } } : { facingMode: opt.facingMode })
      };
      const stream = await navigator.mediaDevices.getUserMedia({ video, audio: false });
      if (S.mode) release();
      S.stream = stream;
      S.track = stream.getVideoTracks()[0];
      S.el = R.video;
      R.video.srcObject = stream;
      await R.video.play().catch(() => {});
      showRunning('camera');
      listDevices();
    } catch (err) {
      R.camError.textContent = CAMERA_ERRORS[err.name] || `無法開啟攝影機（${err.message}）。可以先用示範影像查看效果。`;
    } finally {
      R.startCam.disabled = false;
    }
  }

  function startDemo() {
    if (S.mode) release();
    R.device.hidden = true;
    S.el = R.demo;
    showRunning('demo');
  }

  /** 有兩支以上攝影機時顯示切換選單 */
  async function listDevices() {
    try {
      const cams = (await navigator.mediaDevices.enumerateDevices()).filter((d) => d.kind === 'videoinput');
      if (cams.length < 2) { R.device.hidden = true; return; }
      const current = S.track?.getSettings?.().deviceId;
      R.device.innerHTML = cams.map((d, i) =>
        `<option value="${esc(d.deviceId)}" ${d.deviceId === current ? 'selected' : ''}>${esc(d.label || `攝影機 ${i + 1}`)}</option>`).join('');
      R.device.hidden = false;
    } catch {
      R.device.hidden = true;
    }
  }

  /* ---------- 取樣位置 ---------- */
  function placeReticle() {
    R.reticle.style.left = S.u * 100 + '%';
    R.reticle.style.top = S.v * 100 + '%';
  }

  function onBoxClick(e) {
    if (!S.mode || e.target.closest('.cam-empty')) return;
    const rect = R.camBox.getBoundingClientRect();
    S.u = clamp((e.clientX - rect.left) / rect.width, 0, 1);
    S.v = clamp((e.clientY - rect.top) / rect.height, 0, 1);
    placeReticle();
    hooks.onMove();
  }

  /* ---------- 主迴圈：畫示範影像 → 讀取取樣區 → 換算 ---------- */
  function tick(t) {
    S.raf = requestAnimationFrame(tick);
    if (S.mode === 'demo') drawDemoPattern(demoCtx, t);

    const src = S.el;
    const sw = S.mode === 'camera' ? src.videoWidth : src.width;
    const sh = S.mode === 'camera' ? src.videoHeight : src.height;
    if (!sw || !sh) return;

    const ar = `${sw} / ${sh}`;
    if (R.camBox.style.aspectRatio !== ar) R.camBox.style.aspectRatio = ar;

    const sx = clamp(Math.round(S.u * sw - n / 2), 0, sw - n);
    const sy = clamp(Math.round(S.v * sh - n / 2), 0, sh - n);
    hctx.drawImage(src, sx, sy, n, n, 0, 0, n, n);
    const d = hctx.getImageData(0, 0, n, n).data;
    let r = 0, g = 0, b = 0;
    for (let i = 0; i < d.length; i += 4) { r += d[i]; g += d[i + 1]; b += d[i + 2]; }
    const cnt = d.length / 4;

    if (t - S.lastTag > 500) {
      R.camTag.textContent = `${S.mode === 'camera' ? '攝影機' : '示範影像'}  ${sw}×${sh}`;
      S.lastTag = t;
    }
    hooks.onFrame(measure(Math.round(r / cnt), Math.round(g / cnt), Math.round(b / cnt), hooks.getGains()), t);
  }

  /* ---------- 事件 ---------- */
  const onStartCam = () => startCamera();
  const onDevice = () => startCamera(R.device.value);
  R.startCam.addEventListener('click', onStartCam);
  R.startDemo.addEventListener('click', startDemo);
  R.stop.addEventListener('click', stop);
  R.device.addEventListener('change', onDevice);
  R.camBox.addEventListener('click', onBoxClick);

  return {
    get mode() { return S.mode; },
    get track() { return S.track; },
    stop,
    /** 卸載時呼叫：釋放攝影機 */
    destroy: release
  };
}
