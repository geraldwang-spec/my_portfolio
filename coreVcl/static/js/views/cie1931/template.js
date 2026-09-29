/* =========================================================
 * views/cie1931/template.js — 畫面 HTML
 * ---------------------------------------------------------
 * 需要由程式操作的元素都加上 data-ref="名稱"，
 * index.js 會用 collectRefs() 一次取得。
 * ========================================================= */
import { esc, icon } from '../../utils/dom.js';

/**
 * @param {object} p
 * @param {object} p.nav       config.js 的選單設定
 * @param {object} p.opt       合併後的參數
 * @param {Array}  p.gamuts    色域設定（含 on 狀態）
 * @param {string} p.filterId  白平衡 SVG 濾鏡的 id
 */
export function template({ nav, opt, gamuts, filterId }) {
  const WB = opt.whiteBalance;
  return `
        <div class="tool-head">
          <div>
            <h1>${esc(nav.title || nav.label)}</h1>
            <p>${esc(nav.intro || '')}</p>
          </div>
          <div class="tool-actions">
            <select class="mini-select" data-ref="device" aria-label="選擇攝影機" hidden></select>
            <button class="ghost-btn" data-ref="stop" hidden>停止影像</button>
          </div>
        </div>

        <div class="tool-body">
          <div class="cie-grid">
            <div class="cie-col">
              <div class="cam-box" data-ref="camBox">
                <svg class="wb-svg" aria-hidden="true" width="0" height="0">
                  <filter id="${filterId}" color-interpolation-filters="linearRGB">
                    <feColorMatrix data-ref="wbMatrix" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0"/>
                  </filter>
                </svg>
                <video data-ref="video" autoplay playsinline muted></video>
                <canvas class="demo-canvas" data-ref="demo" width="640" height="480" hidden></canvas>
                <div class="reticle" data-ref="reticle" hidden></div>
                <div class="cam-tag" data-ref="camTag" hidden></div>
                <div class="cam-empty" data-ref="camEmpty">
                  <div class="empty-icon">${icon('camera')}</div>
                  <h2>開啟影像來源</h2>
                  <p>取樣框內的平均顏色會即時換算成 CIE 1931 xy 座標，並標在色度圖上。點擊影像可移動取樣位置。</p>
                  <div class="cam-empty-actions">
                    <button class="primary-btn" data-ref="startCam">開啟攝影機</button>
                    <button class="ghost-btn" data-ref="startDemo">使用示範影像</button>
                  </div>
                  <p class="form-error" data-ref="camError" role="alert"></p>
                </div>
              </div>

              <div class="cards">
                <section class="card">
                  <h3>取樣結果</h3>
                  <div class="readout-main">
                    <span class="swatch" data-ref="swatch"></span>
                    <dl class="readout-big">
                      <div><dt>x, y</dt><dd data-ref="vxy">—</dd></div>
                      <div><dt>相關色溫（估算）</dt><dd data-ref="vcct">—</dd></div>
                    </dl>
                  </div>
                  <dl class="readout-grid">
                    <div><dt>RGB</dt><dd data-ref="vrgb">—</dd></div>
                    <div><dt>HEX</dt><dd data-ref="vhex">—</dd></div>
                    <div><dt>XYZ</dt><dd data-ref="vxyz">—</dd></div>
                  </dl>
                  <p class="note warn" data-ref="dimNote" hidden>取樣區太暗，座標可能不穩定。請增加光線或移到較亮的區域。</p>
                </section>

                <section class="card">
                  <h3>白平衡 <button class="text-btn" data-ref="wbReset" hidden>重設</button></h3>
                  <div class="switch-row">
                    <span>自動</span>
                    <label class="switch">
                      <input type="checkbox" data-ref="wbSwitch" aria-label="手動白平衡" disabled>
                      <span class="track"></span>
                    </label>
                    <span>手動</span>
                  </div>
                  <div class="wb-manual" data-ref="wbManual" hidden>
                    <label class="range">
                      <span class="range-head">色溫 <output data-ref="wbOut">${WB.value}</output><em>K</em></span>
                      <input type="range" class="temp-range" data-ref="wbSlider"
                             min="${WB.min}" max="${WB.max}" step="${WB.step}" value="${WB.value}">
                      <span class="range-ends"><span data-ref="wbMinL">${WB.min} K</span><span data-ref="wbMaxL">${WB.max} K</span></span>
                    </label>
                    <label class="range" data-ref="tintWrap">
                      <span class="range-head">色調 <output data-ref="tintOut">0</output></span>
                      <input type="range" class="tint-range" data-ref="tintSlider" min="${-WB.tintRange}" max="${WB.tintRange}" step="1" value="0">
                      <span class="range-ends"><span>偏綠</span><span>偏洋紅</span></span>
                    </label>
                    <div class="presets" data-ref="presets">
                      ${(WB.presets || []).map((p) => `<button class="chip" data-preset="${p.value}">${esc(p.label)} ${p.value}K</button>`).join('')}
                    </div>
                  </div>
                  <p class="note" data-ref="wbNote">開啟影像來源後即可調整。</p>
                  <p class="note mono" data-ref="wbGains" hidden></p>
                </section>
              </div>
            </div>

            <div class="cie-col">
              <div class="chart-box" data-ref="chartBox">
                <canvas data-ref="base"></canvas>
                <canvas data-ref="overlay"></canvas>
              </div>
              <div class="legend" data-ref="legend">
                ${gamuts.map((g, i) => `
                  <label><input type="checkbox" data-gamut="${i}" ${g.on ? 'checked' : ''}>
                    <i style="background:${esc(g.color)}"></i>${esc(g.label)} 色域</label>`).join('')}
                <label><input type="checkbox" data-ref="trailToggle" checked><i class="trail-key"></i>取樣軌跡</label>
              </div>

              <div class="cards">
                <section class="card">
                  <h3>標記座標點</h3>
                  <div class="project-bar" data-ref="projBar">
                    <label class="project-select">
                      <span>專案</span>
                      <select data-ref="projSel" aria-label="選擇專案"></select>
                    </label>
                    <div class="project-tools">
                      <button class="icon-btn sm" data-ref="projNew" title="新增專案" aria-label="新增專案">${icon('plus')}</button>
                      <button class="icon-btn sm" data-ref="projRename" title="重新命名" aria-label="重新命名專案">${icon('edit')}</button>
                      <button class="icon-btn sm danger" data-ref="projDelete" title="刪除專案" aria-label="刪除專案">${icon('trash')}</button>
                    </div>
                  </div>
                  <div class="project-edit" data-ref="projEdit" hidden>
                    <label>
                      <span data-ref="projEditLabel">新專案名稱</span>
                      <input type="text" data-ref="projName" maxlength="24" placeholder="例如：面板 A 量測">
                    </label>
                    <div class="project-edit-actions">
                      <button class="ghost-btn" data-ref="projCancel">取消</button>
                      <button class="primary-btn" data-ref="projSave">建立專案</button>
                    </div>
                    <p class="form-error" data-ref="projError" role="alert"></p>
                  </div>
                  <button class="primary-btn block" data-ref="markSample" disabled>標記目前取樣點</button>
                  <div class="xy-inputs">
                    <label><span>x</span><input type="number" data-ref="ix" min="0" max="0.85" step="0.0001" value="0.3127"></label>
                    <label><span>y</span><input type="number" data-ref="iy" min="0" max="0.85" step="0.0001" value="0.3290"></label>
                    <label class="wide"><span>名稱（選填）</span><input type="text" data-ref="ilabel" maxlength="16" placeholder="例如：面板白點"></label>
                    <button class="ghost-btn" data-ref="addXY">標記</button>
                  </div>
                  <p class="form-error" data-ref="xyError" role="alert"></p>
                </section>

                <section class="card">
                  <h3>已標記的點 <button class="text-btn" data-ref="clearPts" hidden>全部清除</button></h3>
                  <p class="list-meta" data-ref="plistMeta"></p>
                  <ul class="point-list" data-ref="plist"></ul>
                </section>
              </div>
            </div>
          </div>
        </div>`;
}
