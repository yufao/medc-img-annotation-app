import React, { useEffect, useState } from 'react';
import api from '../../api/client';

export default function ImageSelector({ user, dataset, role, onSelect, onBack, pageSize = 20 }) {
  const [images, setImages] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    setImages([]);
    setPage(1);
    setHasMore(true);
    loadImages(1, true);
  }, [dataset, user]);

  const loadImages = async (pageNum = page, reset = false) => {
    setLoading(true);
    try {
      const { data } = await api.post('/images_with_annotations', {
        dataset_id: dataset.id,
        expert_id: user,
        role: role,
        page: pageNum,
        pageSize,
        include_all: true
      });
      if (reset) setImages(data); else setImages(prev => [...prev, ...data]);
      setHasMore(data.length === pageSize);
    } catch (error) {
      console.error('加载图片失败:', error);
      setImages([]);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    if (!loading && hasMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      loadImages(nextPage, false);
    }
  };

  return (
    <div className="dataset-card">
      <div className="selector-header">
        <h2>选择图片进行标注/修改</h2>
        <button className="btn back-btn" onClick={onBack}>返回</button>
      </div>
      <div style={{maxHeight:500,overflowY:'auto'}}>
        {images.map(img => (
          <div key={img.image_id} className="image-selector-item">
            <img
              src={`/static/img/${img.filename}`}
              alt={`图片ID: ${img.image_id}`}
              className="image-selector-thumb"
              loading="lazy"
              onError={(e) => { e.target.style.display = 'none'; }}
            />
            <div style={{flex:1}}>
              <div className="image-selector-id">图片 ID: #{img.image_id}</div>
              <div className="image-selector-status">
                {img.annotation ? (
                  <span className="status-annotated">
                    ✓ 已标注: {img.annotation.label_name || img.annotation.label}
                    {img.annotation.tip && ` (${img.annotation.tip})`}
                  </span>
                ) : (
                  <span className="status-pending">○ 未标注</span>
                )}
              </div>
            </div>
            <button className="btn" onClick={() => onSelect(img.image_id)}>
              {img.annotation ? '修改标注' : '开始标注'}
            </button>
          </div>
        ))}
        {loading && <div className="loading-text">加载中...</div>}
        {!loading && images.length === 0 && (
          <div className="empty-state">
            <div className="empty-title">暂无图片数据</div>
            <div className="empty-subtitle">请检查数据集是否包含图片，或联系管理员</div>
          </div>
        )}
        {!loading && hasMore && (
          <button className="btn" onClick={handleLoadMore} style={{width:'100%',marginTop:16}}>加载更多</button>
        )}
      </div>
    </div>
  );
}
