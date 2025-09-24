import { create } from 'zustand';

// 全局状态：用户 / 角色 / 当前数据集 / 标签缓存 / 已加载图片分页缓存
export const useAppStore = create((set, get) => ({
  user: null,
  role: '',
  dataset: null,
  labelsCache: {}, // key: datasetId -> labels array
  imagePageCache: {}, // key: datasetId:page -> images list
  setUser: (user, role) => set({ user, role }),
  clearUser: () => set({ user: null, role: '', dataset: null }),
  setDataset: (dataset) => set({ dataset }),
  cacheLabels: (datasetId, labels) => set(state => ({ labelsCache: { ...state.labelsCache, [datasetId]: labels } })),
  getLabelsCached: (datasetId) => get().labelsCache[datasetId],
  cacheImagePage: (datasetId, page, images) => set(state => ({ imagePageCache: { ...state.imagePageCache, [`${datasetId}:${page}`]: images } })),
  getImagePageCached: (datasetId, page) => get().imagePageCache[`${datasetId}:${page}`],
}));

export default useAppStore;
