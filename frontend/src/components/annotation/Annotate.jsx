import React, { useCallback, useEffect, useState, useRef } from 'react';
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
  // 预取下一张（稳定随机顺序）：候选元数据 + 已预加载的图片 URL
  const [nextCandidate, setNextCandidate] = useState(null);
  const [nextImgSrc, setNextImgSrc] = useState(null);
  // 导航历史：确保“上一张”回到用户实际浏览的上一项（而非服务端重新计算的上一项）
  const historyRef = useRef({ stack: [], idx: -1 });

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

  // 预取下一张（按稳定随机顺序：include_all=false 的顺序）
  const prefetchNextStableRandom = useCallback(async (currentImageId) => {
    if (!dataset || !user) return;
    try {
      const resp = await api.post('/images_with_annotations', { dataset_id: dataset.id, expert_id: user, role, include_all: false });
      const list = (resp.data || []).filter(x => !x.annotation);
      if (!list.length) { setNextCandidate(null); setNextImgSrc(null); return; }
      // 在未标注序列中找到当前的索引；通常 current 在未标注列表的第 0 位
      const idx = list.findIndex(x => String(x.image_id) === String(currentImageId));
      const nextItem = idx >= 0 ? list[idx + 1] : list[0];
      if (nextItem) {
        setNextCandidate({ image_id: nextItem.image_id, filename: nextItem.filename, image_path: nextItem.image_path });
        // 通过 JS 预加载下一张图片
        const url = `/static/img/${nextItem.filename}`;
        const imgEl = new Image();
        imgEl.loading = 'eager';
        imgEl.decoding = 'async';
        imgEl.src = url;
        // 预加载完成/失败都记录 URL（失败时浏览器也会缓存 404/错误状态，后续渲染仍会触发请求）
        imgEl.onload = () => setNextImgSrc(url);
        imgEl.onerror = () => setNextImgSrc(url);
      } else {
        setNextCandidate(null); setNextImgSrc(null);
      }
    } catch (e) {
      // 忽略预取失败，不影响主流程
      setNextCandidate(null); setNextImgSrc(null);
    }
  }, [dataset, user, role]);

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

  const setCurrentImage = useCallback((meta, { push } = { push: false }) => {
    if (!meta || !meta.image_id) return;
    setImg({ image_id: meta.image_id, filename: meta.filename });
    setImageId(meta.image_id);
    if (meta.annotation) {
      setLabel(String(meta.annotation.label));
      setRemark(meta.annotation.tip || '');
    } else {
      setLabel('');
      setRemark('');
    }
    resetView();
    setIsImageSelected(false);
    // 维护历史栈
    const h = historyRef.current;
    if (push) {
      // 若当前不在栈尾，截断前进分支
      if (h.idx < h.stack.length - 1) h.stack = h.stack.slice(0, h.idx + 1);
      if (h.stack.length === 0 || String(h.stack[h.stack.length - 1]) !== String(meta.image_id)) {
        h.stack.push(meta.image_id);
      }
      h.idx = h.stack.length - 1;
    }
  }, []);

  const fetchImage = async (id) => {
    setIsLoading(true); setError(null);
    try {
      if (id) {
        const { data } = await api.post('/images_with_annotations', { dataset_id: dataset.id, expert_id: user, role, include_all: true });
        const found = data.find(img => String(img.image_id) === String(id));
        if (found) {
          setCurrentImage(found, { push: historyRef.current.idx < 0 });
          // 基于当前图片预取下一张
          prefetchNextStableRandom(found.image_id);
          return;
        }
      }
      // 优先仅请求未标注图片列表，以遵循后端“稳定随机顺序”
      const unAnnotatedResp = await api.post('/images_with_annotations', { dataset_id: dataset.id, expert_id: user, role, include_all: false });
      const unAnnotatedList = (unAnnotatedResp.data || []).filter(x => !x.annotation);
      if (unAnnotatedList.length > 0) {
        const first = unAnnotatedList[0];
        setCurrentImage(first, { push: true });
        // 直接用列表中的第二项作为“下一张”进行预取（稳定随机顺序）
        const second = unAnnotatedList[1];
        if (second) {
          setNextCandidate({ image_id: second.image_id, filename: second.filename, image_path: second.image_path });
          const url = `/static/img/${second.filename}`;
          const imgEl = new Image(); imgEl.loading = 'eager'; imgEl.decoding = 'async'; imgEl.src = url;
          imgEl.onload = () => setNextImgSrc(url);
          imgEl.onerror = () => setNextImgSrc(url);
        } else { setNextCandidate(null); setNextImgSrc(null); }
      }
      else {
        try {
          const statsResponse = await api.get(`/datasets/${dataset.id}/statistics`, { params: { expert_id: user, role, dataset_id: dataset.id } });
          const stats = statsResponse.data; if ((stats.annotated_count || 0) >= (stats.total_count || 0) && stats.total_count > 0) { setImg({ completed: true }); setImageId(null); }
          else {
            const nextImageResponse = await api.post('/next_image', { expert_id: user, dataset_id: dataset.id, role });
            if (nextImageResponse.data.image_id) {
              const meta = { image_id: nextImageResponse.data.image_id, filename: nextImageResponse.data.filename };
              setCurrentImage(meta, { push: true });
              prefetchNextStableRandom(meta.image_id);
            } else { setImg({ completed: true }); setImageId(null); }
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
      // 优先使用“已预取的下一张”（稳定随机序的下一项）
      let usedOptimistic = false;
      if (nextCandidate) {
        setCurrentImage({ image_id: nextCandidate.image_id, filename: nextCandidate.filename }, { push: true });
        usedOptimistic = true;
      }
      // 后台校验：请求 authoritative 的 next_image，若与预取不一致则切换为权威结果
      try {
        const nextImageResponse = await api.post('/next_image', { expert_id: user, dataset_id: dataset.id, role });
        if (nextImageResponse.data.image_id) {
          const authoritative = { image_id: nextImageResponse.data.image_id, filename: nextImageResponse.data.filename };
          if (!usedOptimistic || String(authoritative.image_id) !== String(nextCandidate?.image_id)) {
            setCurrentImage(authoritative, { push: true });
          }
          // 基于新 current 继续预取后续项
          prefetchNextStableRandom(authoritative.image_id);
        } else {
          // 没有下一张
          if (!usedOptimistic) { setImg({ completed: true }); setImageId(null); }
          setNextCandidate(null); setNextImgSrc(null);
        }
      } catch {
        // 如果 next_image 失败，但已使用本地预取，则继续基于本地 current 进行预取；否则回退到拉取未标注列表
        if (usedOptimistic) {
          prefetchNextStableRandom(nextCandidate.image_id);
        } else {
          fetchImage();
        }
      }
      fetchCounts(true);
    } catch { setError('提交失败，请重试'); }
    finally { setSubmitDisabled(false); }
  };

  const handlePrev = async () => {
    // 使用服务端“最近一次标注”的语义获取上一张，避免仅按浏览历史或顺序回退
    if (!dataset || !user) return;
    setIsLoading(true); setError(null);
    try {
      const body = { dataset_id: dataset.id, expert_id: user, role, by: 'last_annotated' };
      if (img?.image_id) body.current_image_id = img.image_id; // 避免返回当前同一张
      const resp = await api.post('/prev_image', body);
      const data = resp.data || {};
      if (data.image_id) {
        const meta = { image_id: data.image_id, filename: data.filename };
        setCurrentImage(meta, { push: true });
        prefetchNextStableRandom(meta.image_id);
      } else {
        setError('没有上一张可回退');
      }
    } catch (e) {
      setError('获取上一张失败，请重试');
    } finally {
      setIsLoading(false);
    }
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
          <img
            key={`${img.image_id}-${img.filename || ''}`}
            src={`/static/img/${img.filename}?v=${img.image_id}`}
            alt={`图片ID: ${img.image_id}`}
            loading="lazy"
            draggable={false}
            style={{
              transform: `scale(${imageScale}) translate(${imageOffset.x / imageScale}px, ${imageOffset.y / imageScale}px)`,
              cursor: imageScale > 1 ? (isDragging ? 'grabbing' : 'grab') : (isImageSelected ? 'zoom-in' : 'pointer'),
              transition: isDragging ? 'none' : 'transform 0.1s ease',
              userSelect: 'none'
            }}
          />
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
      <button
        className={"btn" + (submitDisabled ? " pending" : "")}
        onClick={handleSubmit}
        disabled={!label && !submitDisabled}
        style={{ pointerEvents: submitDisabled ? 'none' : 'auto' }}
      >
        {submitDisabled ? '提交中...' : '提交并下一张'}
      </button>
      <button className="btn" onClick={handlePrev} style={{ marginLeft: 12 }}>上一张</button>
    </div>
  );
}
