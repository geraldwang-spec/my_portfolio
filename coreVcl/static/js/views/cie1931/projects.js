/* =========================================================
 * views/cie1931/projects.js — 「標記座標點」與「已標記的點」卡片
 * ---------------------------------------------------------
 * 專案選單（新增 / 重新命名 / 刪除）、標記取樣點、輸入 xy 標記、點清單
 * 資料存取交給 projects-store.js
 * ========================================================= */
import { esc, icon } from '../../utils/dom.js';
import { xyToDisplayColor } from '../../utils/color.js';
import { RANGE } from './cmf-data.js';
import { createProjectStore } from './projects-store.js';

/**
 * @param {object} R    畫面元素
 * @param {object} opt  參數（projects）
 * @param {object} hooks
 * @param {() => object|null} hooks.getSample  目前取樣結果
 * @param {() => void} hooks.onChange          標記點改變（重畫色度圖）
 */
export function createProjects(R, opt, hooks) {
  const store = createProjectStore(opt.projects);
  let editMode = null;   // 'new' | 'rename' | null

  /* ---------- 畫面 ---------- */
  function render() {
    const cur = store.active;
    R.projSel.innerHTML = store.projects.map((p) =>
      `<option value="${esc(p.id)}" ${p.id === cur.id ? 'selected' : ''}>${esc(p.name)}（${p.points.length}）</option>`).join('');

    const pts = store.points;
    R.plistMeta.textContent = `${cur.name}，共 ${pts.length} 個點`;
    R.clearPts.hidden = !pts.length;
    R.plist.innerHTML = pts.length ? pts.map((p, i) => `
      <li>
        <span class="dot" style="background:${p.color}"></span>
        <span class="pt-info"><b>${esc(p.label)}</b><small>x ${p.x.toFixed(4)}　y ${p.y.toFixed(4)}</small></span>
        <button class="close-btn" data-remove="${i}" aria-label="移除 ${esc(p.label)}">${icon('close')}</button>
      </li>`).join('') : '<li class="empty-row">這個專案還沒有標記點。標記取樣點或輸入 xy 座標後會列在這裡。</li>';
    hooks.onChange();
  }

  /* ---------- 專案編輯（新增 / 重新命名） ---------- */
  function openEdit(mode) {
    editMode = mode;
    R.projError.textContent = '';
    R.projEditLabel.textContent = mode === 'new' ? '新專案名稱' : '專案名稱';
    R.projSave.textContent = mode === 'new' ? '建立專案' : '儲存名稱';
    R.projName.value = mode === 'rename' ? store.active.name : '';
    R.projBar.hidden = true;
    R.projEdit.hidden = false;
    R.projName.focus();
    R.projName.select();
  }

  function closeEdit() {
    editMode = null;
    R.projEdit.hidden = true;
    R.projBar.hidden = false;
  }

  function saveEdit() {
    const name = R.projName.value.trim();
    if (!name) { R.projError.textContent = '請輸入專案名稱。'; return; }
    if (store.nameTaken(name, editMode === 'rename' ? store.active.id : null)) {
      R.projError.textContent = '已有同名的專案，請換一個名稱。';
      return;
    }
    if (editMode === 'new') store.create(name); else store.rename(name);
    closeEdit();
    render();
  }

  function removeProject() {
    const cur = store.active;
    const msg = cur.points.length
      ? `確定要刪除專案「${cur.name}」和其中 ${cur.points.length} 個標記點嗎？此動作無法復原。`
      : `確定要刪除專案「${cur.name}」嗎？`;
    if (!confirm(msg)) return;
    store.removeActive();
    render();
  }

  /* ---------- 標記點 ---------- */
  function markSample() {
    const s = hooks.getSample();
    if (!s || s.x == null) return;
    store.addPoint({ x: s.x, y: s.y, label: `取樣 ${store.points.length + 1}`, color: `rgb(${s.r},${s.g},${s.b})` });
    render();
  }

  function addXY() {
    const x = parseFloat(R.ix.value), y = parseFloat(R.iy.value);
    if (!(x >= 0 && x <= RANGE && y > 0 && y <= RANGE)) {
      R.xyError.textContent = `x、y 需介於 0 到 ${RANGE} 之間，請重新輸入。`;
      return;
    }
    R.xyError.textContent = '';
    store.addPoint({
      x, y,
      label: R.ilabel.value.trim() || `點 ${store.points.length + 1}`,
      color: xyToDisplayColor(x, y)
    });
    R.ilabel.value = '';
    render();
  }

  /* ---------- 事件 ---------- */
  R.projSel.addEventListener('change', () => { store.select(R.projSel.value); render(); });
  R.projNew.addEventListener('click', () => openEdit('new'));
  R.projRename.addEventListener('click', () => openEdit('rename'));
  R.projDelete.addEventListener('click', removeProject);
  R.projCancel.addEventListener('click', closeEdit);
  R.projSave.addEventListener('click', saveEdit);
  R.projName.addEventListener('keydown', (e) => {
    if (e.isComposing) return;
    if (e.key === 'Enter') { e.preventDefault(); saveEdit(); }
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeEdit(); }
  });

  R.markSample.addEventListener('click', markSample);
  R.addXY.addEventListener('click', addXY);
  [R.ix, R.iy, R.ilabel].forEach((inp) => inp.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); addXY(); }
  }));
  R.plist.addEventListener('click', (e) => {
    const b = e.target.closest('[data-remove]');
    if (b) { store.removePoint(Number(b.dataset.remove)); render(); }
  });
  R.clearPts.addEventListener('click', () => {
    if (!confirm(`確定要清除專案「${store.active.name}」的所有標記點嗎？`)) return;
    store.clearPoints();
    render();
  });

  render();

  return {
    /** 目前專案的標記點（給色度圖使用） */
    get points() { return store.points; },
    /** 有影像時才能標記取樣點 */
    setSampleAvailable(ok) { R.markSample.disabled = !ok; }
  };
}
