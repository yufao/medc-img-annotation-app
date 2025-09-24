import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

// 兼容新旧两种后端响应格式：
// 1) 旧格式: 直接返回数组或对象 / { msg: 'success', ... }
// 2) 新格式: { code:'ok', message:'success', data: <payload> }
// 处理逻辑：若检测到包装格式，则将 r.data 替换为内部 payload，并为对象型 payload 附加 msg 字段
api.interceptors.response.use(r => {
  const d = r.data;
  if (d && typeof d === 'object' && 'code' in d && 'message' in d) {
    if ('data' in d) {
      let inner = d.data;
      if (inner && typeof inner === 'object' && !Array.isArray(inner)) {
        // 保持前端既有判断 res.data.msg === 'success' 的兼容
        inner.msg = d.message;
      }
      // 对于数组，直接覆盖即可；数组上不强制挂 msg 避免影响遍历
      r.data = inner;
    } else {
      r.data = { msg: d.message };
    }
  }
  return r;
}, err => Promise.reject(err));

export const Api = {
  listDatasets: () => api.get('/datasets'),
  datasetStatistics: (datasetId, expertId) => api.get(`/datasets/${datasetId}/statistics`, { params: { expert_id: expertId } }),
  createDataset: (body) => api.post('/admin/datasets', body),
  updateDatasetMultiSelect: (id, multi, role='admin') => api.patch(`/admin/datasets/${id}/multi-select`, { multi_select: multi, role }),
  recountDataset: (id, role='admin') => api.post(`/admin/datasets/${id}/recount`, { role }),
  listLabels: (datasetId) => api.get('/labels', { params: { dataset_id: datasetId } }),
  imagesWithAnnotations: (body) => api.post('/images_with_annotations', body),
  nextImage: (body) => api.post('/next_image', body),
  prevImage: (body) => api.post('/prev_image', body),
  annotate: (body) => api.post('/annotate', body),
  updateAnnotation: (body) => api.post('/update_annotation', body),
  exportExcel: (datasetId, expertId) => api.get('/export', { params: { dataset_id: datasetId, expert_id: expertId }, responseType: 'blob' }),
  listUsers: (role='admin') => api.get('/admin/users', { params: { role } }),
  userConfig: (role='admin') => api.get('/admin/users/config', { params: { role } })
};

export default api;
