/* =========================================================
 * views/cie1931/projects-store.js — 專案與標記點的資料層
 * ---------------------------------------------------------
 * 只處理資料與儲存，不碰畫面。之後若要改存到後端，只需要改這個檔案。
 *
 * 資料格式：
 * { activeId, projects: [{ id, name, created, points: [{ x, y, label, color, time }] }] }
 * ========================================================= */
import * as storage from '../../utils/storage.js';

const newId = () => 'p' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
const newProject = (name) => ({ id: newId(), name, created: new Date().toISOString(), points: [] });

/**
 * @param {{ storageKey: string, defaultName: string }} cfg
 */
export function createProjectStore(cfg) {
  let data = storage.getJSON(cfg.storageKey, null);
  if (!data || !Array.isArray(data.projects) || !data.projects.length) {
    const first = newProject(cfg.defaultName);
    data = { activeId: first.id, projects: [first] };
  }
  const save = () => storage.setJSON(cfg.storageKey, data);

  const store = {
    get projects() { return data.projects; },
    get active() { return data.projects.find((p) => p.id === data.activeId) || data.projects[0]; },
    get points() { return store.active.points; },

    select(id) { data.activeId = id; save(); },

    /** 名稱是否已被其他專案使用 */
    nameTaken(name, exceptId = null) {
      return data.projects.some((p) => p.name === name && p.id !== exceptId);
    },

    create(name) {
      const p = newProject(name);
      data.projects.push(p);
      data.activeId = p.id;
      save();
      return p;
    },

    rename(name) { store.active.name = name; save(); },

    /** 刪除目前專案；刪到沒有專案時自動建立空的預設專案 */
    removeActive() {
      data.projects = data.projects.filter((p) => p.id !== data.activeId);
      if (!data.projects.length) data.projects.push(newProject(cfg.defaultName));
      data.activeId = data.projects[0].id;
      save();
    },

    addPoint(point) {
      store.points.push({ ...point, time: new Date().toISOString() });
      save();
    },

    removePoint(index) { store.points.splice(index, 1); save(); },

    clearPoints() { store.points.length = 0; save(); }
  };
  return store;
}
