import React, { useCallback, useEffect, useState } from 'react';
import api from '../../api/client';

// 提取：进度环组件
function ProgressStats({ annotatedCount, totalCount }) {
  return (
    <div className="progress-section">
      <div className="progress-info">
        <div className="progress-text-card">
          <div className="progress-stats">
            <div className="stat-item completed"><span className="stat-number">{annotatedCount}</span><span className="stat-label">已标注</span></div>
            <div className="stat-divider">|</div>
            <div className="stat-item remaining"><span className="stat-number">{Math.max(0, totalCount - annotatedCount)}</span><span className="stat-label">剩余</span></div>
            <div className="stat-divider">|</div>
            <div className="stat-item total"><span className="stat-number">{totalCount}</span><span className="stat-label">总计</span></div>
          </div>
        </div>
      </div>
      <div className="progress-visual">
        <div className="progress-circle">
          <svg width="90" height="90" viewBox="0 0 90 90">
            <circle cx="45" cy="45" r="35" fill="none" stroke="#e0e7ff" strokeWidth="8" />
            <circle cx="45" cy="45" r="35" fill="none" stroke="url(#progressGradient)" strokeWidth="8" strokeDasharray={`${2 * Math.PI * 35}`} strokeDashoffset={`${2 * Math.PI * 35 * (1 - (totalCount > 0 ? annotatedCount / totalCount : 0))}`} transform="rotate(-90 45 45)" style={{ transition: 'stroke-dashoffset 0.5s ease' }} strokeLinecap="round" />
            <defs>
              <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#1677ff" />
                <stop offset="100%" stopColor="#4f8cff" />
              </linearGradient>
            </defs>
          </svg>
          <div className="progress-percentage">{totalCount > 0 ? Math.round((annotatedCount / totalCount) * 100) : 0}%</div>
        </div>
      </div>
    </div>
  );
}

export default function Annotate({ user, dataset, role, onDone, imageIdInit, onSelectMode }) {
  const [img, setImg] = useState(null);
  const [labels, setLabels] = useState([]);
  const [label, setLabel] = useState('');
  const [remark, setRemark] = useState('');
  const [imageId, setImageId] = useState(imageIdInit);
  const [annotatedCount, setAnnotatedCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [imageScale, setImageScale] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });
  const [isImageSelected, setIsImageSelected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [submitDisabled, setSubmitDisabled] = useState(false);
  const [countsCache, setCountsCache] = useState(null);
  const [lastCountsUpdate, setLastCountsUpdate] = useState(0);

  // 加载标签 & 统计
  useEffect(() => {
    if (dataset) {
      api.get('/labels', { params: { dataset_id: dataset.id } })
        .then(r => { const ls = r.data || []; setLabels(ls); if (!ls.length) setError('该数据集还没有配置标签，请联系管理员添加标签'); else setError(null); })
        .catch(() => { setLabels([]); setError('获取标签失败，请重试'); });
      fetchCounts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataset]);

  useEffect(() => { if (imageIdInit) { setImageId(imageIdInit); fetchImage(imageIdInit); } }, [imageIdInit]);
  useEffect(() => { if (dataset && user && !imageIdInit) fetchImage(imageId || null); // eslint-disable-next-line
  }, [dataset, user]);

  const fetchCounts = async (forceRefresh = false) => {
    if (!dataset || !user) return;
    const now = Date.now();
    if (!forceRefresh && countsCache && (now - lastCountsUpdate < 5000)) {
      setAnnotatedCount(countsCache.annotated_count); setTotalCount(countsCache.total_count); return;
    }
    try {
      const response = await api.get(`/datasets/${dataset.id}/statistics`, { params: { expert_id: user, role, dataset_id: dataset.id } });
      const stats = response.data;
      const counts = { annotated_count: stats.annotated_count || 0, total_count: stats.total_count || 0 };
      setAnnotatedCount(counts.annotated_count); setTotalCount(counts.total_count); setCountsCache(counts); setLastCountsUpdate(now);
    } catch (e) { setTimeout(() => { if (dataset && user) fetchCounts(true); }, 3000); }
  };

  const fetchImage = async (id) => {
    setIsLoading(true); setError(null);
    try {
      if (id) {
        const { data } = await api.post('/images_with_annotations', { dataset_id: dataset.id, expert_id: user, role, include_all: true });
        const found = data.find(img => String(img.image_id) === String(id));
        if (found) { setImg(found); if (found.annotation) { setLabel(String(found.annotation.label)); setRemark(found.annotation.tip || ''); } else { setLabel(''); setRemark(''); } setImageId(found.image_id); resetView(); setIsImageSelected(false); return; }
      }
      const allImagesResponse = await api.post('/images_with_annotations', { dataset_id: dataset.id, expert_id: user, role, include_all: true });
      const allImages = allImagesResponse.data;
      const unAnnotatedImage = allImages.find(img => !img.annotation);
      if (unAnnotatedImage) { setImg(unAnnotatedImage); setLabel(''); setRemark(''); setImageId(unAnnotatedImage.image_id); resetView(); setIsImageSelected(false); }
      else {
        try {
          const statsResponse = await api.get(`/datasets/${dataset.id}/statistics`, { params: { expert_id: user, role, dataset_id: dataset.id } });
          const stats = statsResponse.data; if ((stats.annotated_count || 0) >= (stats.total_count || 0) && stats.total_count > 0) { setImg({ completed: true }); setImageId(null); }
          else {
            const nextImageResponse = await api.post('/next_image', { expert_id: user, dataset_id: dataset.id, role });
            if (nextImageResponse.data.image_id) { setImg({ image_id: nextImageResponse.data.image_id, filename: nextImageResponse.data.filename }); setLabel(''); setRemark(''); setImageId(nextImageResponse.data.image_id); resetView(); setIsImageSelected(false); } else { setImg({ completed: true }); setImageId(null); }
          }
        } catch { setImg({ completed: true }); setImageId(null); }
      }
    } catch (e) { setError('加载图片失败，请重试'); setImg(null); } finally { setIsLoading(false); }
  };

  const resetView = () => { setImageScale(1); setImageOffset({ x: 0, y: 0 }); };

  const handleSubmit = async () => {
    if (!label) { setError('请选择标签'); return; }
    if (submitDisabled) return; setSubmitDisabled(true); setError(null);
    try {
      await api.post('/annotate', { expert_id: user, dataset_id: dataset.id, image_id: img.image_id, label, tip: remark });
      setLabel(''); setRemark('');
      try {
        const allImagesResponse = await api.post('/images_with_annotations', { dataset_id: dataset.id, expert_id: user, role, include_all: true });
        const allImages = allImagesResponse.data; const unAnnotatedImage = allImages.find(img => !img.annotation);
        if (unAnnotatedImage) { setImg(unAnnotatedImage); setImageId(unAnnotatedImage.image_id); resetView(); setIsImageSelected(false); }
        else {
          const statsResponse = await api.get(`/datasets/${dataset.id}/statistics`, { params: { expert_id: user, role, dataset_id: dataset.id } });
            const stats = statsResponse.data; if ((stats.annotated_count || 0) >= (stats.total_count || 0) && stats.total_count > 0) { setImg({ completed: true }); setImageId(null); }
            else {
              const nextImageResponse = await api.post('/next_image', { expert_id: user, dataset_id: dataset.id, role });
              if (nextImageResponse.data.image_id) { setImg({ image_id: nextImageResponse.data.image_id, filename: nextImageResponse.data.filename }); setImageId(nextImageResponse.data.image_id); resetView(); setIsImageSelected(false); }
              else { setImg({ completed: true }); setImageId(null); }
            }
        }
      } catch { fetchImage(); }
      fetchCounts(true);
    } catch { setError('提交失败，请重试'); }
    finally { setTimeout(() => setSubmitDisabled(false), 1000); }
  };

  const handlePrev = async () => {
    try { const { data } = await api.post('/prev_image', { dataset_id: dataset.id, image_id: img.image_id }); if (data.image_id) fetchImage(data.image_id); } catch (e) { console.error('获取上一张图片失败'); }
  };

  // 交互：拖拽与缩放
  const onImageMouseDown = e => { setIsImageSelected(true); if (imageScale > 1) { e.preventDefault(); setIsDragging(true); setDragStart({ x: e.clientX - imageOffset.x, y: e.clientY - imageOffset.y }); } };
  const onImageMouseMove = e => { if (isDragging && imageScale > 1) { e.preventDefault(); const newX = e.clientX - dragStart.x; const newY = e.clientY - dragStart.y; setImageOffset({ x: newX, y: newY }); } };
  const onImageMouseUp = () => setIsDragging(false);

  if (isLoading) return <div className="loading-box"><div className="loading-spinner"></div><p>正在加载图片...</p></div>;
  if (error) return <div className="error-box"><p className="error-message">❌ {error}</p><button className="btn" onClick={() => { setError(null); fetchImage(imageId); }}>重试</button><button className="btn secondary" onClick={onDone}>返回</button></div>;
  if (!img) return <div className="done-box">标注完成！<button className="btn" onClick={onDone}>返回</button></div>;
  if (img.completed) return (
    <div className="completion-overlay"><div className="completion-card"><div className="completion-icon">🎉</div><h2 className="completion-title">恭喜！</h2><p className="completion-message">本数据集已全部标注完成</p><div className="completion-stats"><span className="completion-stat"><strong>{annotatedCount}</strong> 张图片已完成标注</span></div><div className="completion-actions"><button className="btn completion-btn secondary" onClick={() => onSelectMode && onSelectMode()}>继续查看本数据集</button><button className="btn completion-btn" onClick={onDone}>返回数据集选择</button></div></div></div>
  );

  return (
    <div className="annotate-box">
      <ProgressStats annotatedCount={annotatedCount} totalCount={totalCount} />
      <h2>标注图片: ID #{img.image_id}</h2>
      <div className="image-container" onClick={e => { if (e.target === e.currentTarget) setIsImageSelected(false); }}>
        <div className={`image-viewer ${isImageSelected ? 'selected' : ''}`} onMouseDown={onImageMouseDown} onMouseMove={onImageMouseMove} onMouseUp={onImageMouseUp}>
          <img src={`/static/img/${img.filename}`} alt={`图片ID: ${img.image_id}`} loading="lazy" draggable={false} style={{ transform: `scale(${imageScale}) translate(${imageOffset.x / imageScale}px, ${imageOffset.y / imageScale}px)`, cursor: imageScale > 1 ? (isDragging ? 'grabbing' : 'grab') : (isImageSelected ? 'zoom-in' : 'pointer'), transition: isDragging ? 'none' : 'transform 0.1s ease', userSelect: 'none' }} />
        </div>
        <div className="image-controls">
          <div className="control-buttons">
            <button className="control-btn" onClick={() => setImageScale(p => Math.max(0.3, p - 0.2))}>-</button>
            <span className="scale-text">{Math.round(imageScale * 100)}%</span>
            <button className="control-btn" onClick={() => setImageScale(p => Math.min(3, p + 0.2))}>+</button>
            <button className="control-btn reset-btn" onClick={() => { setImageScale(1); setImageOffset({ x: 0, y: 0 }); setIsImageSelected(false); }}>重置</button>
          </div>
        </div>
        <div className="img-id">图片 ID: #{img.image_id}</div>
      </div>
      <div className="form-row label-row">
        <label>标签：</label>
        <div className="label-btn-group">
          {labels.length === 0 ? (<div style={{color: '#999', fontSize: '14px', padding: '10px'}}>{error || '正在加载标签...'}</div>) : labels.map(l => {
            const isSelected = String(label) === String(l.label_id || l.id);
            return <button key={l.label_id || l.id} type="button" className={"label-btn" + (isSelected ? " selected" : "")} onClick={() => { setLabel(String(l.label_id || l.id)); setError(null); }}>{l.name}</button>;
          })}
        </div>
      </div>
      <div className="form-row">
        <label>备注：</label>
        <input className="input" value={remark} onChange={e => setRemark(e.target.value)} placeholder="可选" />
      </div>
      <button className="btn" onClick={handleSubmit} disabled={!label || submitDisabled} style={{ opacity: submitDisabled ? 0.6 : 1 }}>{submitDisabled ? '提交中...' : '提交并下一张'}</button>
      <button className="btn" onClick={handlePrev} style={{ marginLeft: 12 }}>上一张</button>
    </div>
  );
}
