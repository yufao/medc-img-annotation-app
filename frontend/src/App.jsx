import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import DatasetSelect from './components/DatasetSelect';
import DatasetManager from './components/admin/DatasetManager';
import ImageSelector from './components/annotation/ImageSelector';
import Annotate from './components/annotation/Annotate';
import ExportButton from './components/annotation/ExportButton';

export default function App() {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState('');
  const [dataset, setDataset] = useState(null);
  const [selectMode, setSelectMode] = useState(false);
  const [selectedImageId, setSelectedImageId] = useState(null);
  const [showDatasetManager, setShowDatasetManager] = useState(false);

  const handleLogin = (u, r) => { setUser(u); setRole(r); };
  const handleLogout = () => { setUser(null); setDataset(null); setShowDatasetManager(false); };
  const handleBackOrLogout = () => {
    if (dataset && !selectMode) { setDataset(null); setSelectedImageId(null); return; }
    if (showDatasetManager) { setShowDatasetManager(false); return; }
    if (selectMode) { setSelectMode(false); return; }
    handleLogout();
  };
  const handleImageSelect = (id) => { setSelectedImageId(id); setSelectMode(false); };
  const handleAnnotationDone = () => { setDataset(null); setSelectedImageId(null); };

  if (!user) return <div className="login-bg"><Login onLogin={handleLogin} /></div>;
  if (showDatasetManager) return <div className="select-bg"><DatasetManager user={user} role={role} onBack={() => setShowDatasetManager(false)} /></div>;
  if (!dataset) return <div className="select-bg"><DatasetSelect user={user} role={role} onSelect={setDataset} onAdmin={() => role === 'admin' && setShowDatasetManager(true)} /></div>;
  if (selectMode) return <div className="select-bg"><ImageSelector user={user} dataset={dataset} role={role} onSelect={handleImageSelect} onBack={() => setSelectMode(false)} /></div>;

  return (
    <div className="app-container">
      <div className="page-logos">
        <div className="logo-left"><img src="/实验室LOGO.png" alt="实验室LOGO" className="page-logo" /></div>
        <div className="logo-right"><img src="/JNU-LOGO.jpg" alt="学校LOGO" className="page-logo" /></div>
      </div>
      <div className="main-bg">
        <div className="top-bar">
          <span>用户: <b>{user}</b> ({role})</span>
            <span className="app-title">医学图像标注系统</span>
          <button className="btn logout" onClick={handleBackOrLogout}>{dataset && !selectMode ? '返回' : showDatasetManager ? '返回' : selectMode ? '返回' : '退出'}</button>
        </div>
        <Annotate user={user} dataset={dataset} role={role} onDone={handleAnnotationDone} imageIdInit={selectedImageId} onSelectMode={() => setSelectMode(true)} />
        <div className="export-bar">
          <ExportButton dataset={dataset} user={user} role={role} />
          <button className="btn" onClick={() => setSelectMode(true)}>选择图片/修改标注</button>
        </div>
      </div>
    </div>
  );
}

function DatasetSelect({ user, role, onSelect, onAdmin }) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDatasets = async () => {
      setLoading(true);
      try {
        const response = await api.get('/datasets', {
          params: { user_id: user }
        });
        setDatasets(response.data || []);
      } catch (error) {
        console.error('获取数据集失败:', error);
        setDatasets([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDatasets();
  }, [user]);

  if (loading) {
    return (
      <div className="dataset-card">
        <h2>加载中...</h2>
        <div style={{textAlign:'center',padding:32}}>正在获取可用数据集...</div>
      </div>
    );
  }

  return (
    <div className="dataset-card">
      <h2>选择数据集任务</h2>
      {role === 'admin' && (
        <div className="admin-option">
          <button className="btn admin-btn" onClick={onAdmin}>
            管理数据集
          </button>
        </div>
      )}
      {datasets.length === 0 ? (
        <div style={{textAlign:'center',padding:32}}>
          <div style={{fontSize:18,color:'#999',marginBottom:16}}>暂无可用数据集</div>
          <div style={{fontSize:14,color:'#666'}}>请联系管理员分配数据集任务</div>
        </div>
      ) : (
        <div className="dataset-btn-group">
          {datasets.map((ds, index) => (
            <button
              key={ds.id || ds.name || index} // 使用更安全的 key 生成方式
              className="dataset-btn"
              onClick={() => onSelect(ds)}
            >{ds.name}</button>
          ))}
        </div>
      )}
    </div>
  );
}

function Annotate({ user, dataset, role, onDone, imageIdInit, onSelectMode }) {
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
  const [isImageHovered, setIsImageHovered] = useState(false);
  const [isImageSelected, setIsImageSelected] = useState(false);
  
  // 添加加载状态和错误状态
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [submitDisabled, setSubmitDisabled] = useState(false);

  // 监听 imageIdInit 变化，强制切换图片
  useEffect(() => {
    if (imageIdInit) {
      setImageId(imageIdInit);
      fetchImage(imageIdInit);
    }
  }, [imageIdInit]);

  useEffect(() => {
    if (dataset) {
      console.log("开始获取数据集标签，dataset:", dataset);
      api.get('/labels', { params: { dataset_id: dataset.id } }).then(r => {
        console.log("标签API原始响应:", r);
        console.log("标签数据:", r.data);
        const labelsData = r.data || [];
        setLabels(labelsData);
        if (labelsData.length === 0) {
          console.error(`数据集 ${dataset.id} 没有配置标签。`);
          setError("该数据集还没有配置标签，请联系管理员添加标签");
        } else {
          console.log("成功获取到的标签列表:", labelsData);
          setError(null); // 清除之前的错误
        }
      }).catch(err => {
        console.error("获取标签失败:", err);
        setLabels([]);
        setError("获取标签失败，请重试");
      });
      // 获取计数信息
      fetchCounts();
    }
  }, [dataset]);

  // 添加缓存变量
  const [countsCache, setCountsCache] = useState(null);
  const [lastCountsUpdate, setLastCountsUpdate] = useState(0);

  const fetchCounts = async (forceRefresh = false) => {
    if (!dataset || !user) return;
    
    // 缓存5秒内的数据，避免频繁请求
    const now = Date.now();
    if (!forceRefresh && countsCache && (now - lastCountsUpdate < 5000)) {
      setAnnotatedCount(countsCache.annotated_count);
      setTotalCount(countsCache.total_count);
      return;
    }
    
    try {
      console.log(`获取数据集${dataset.id}的统计信息...`);
      const response = await api.get(`/datasets/${dataset.id}/statistics`, {
        params: { 
          expert_id: user, 
          role: role,
          dataset_id: dataset.id // 明确指定数据集ID
        }
      });
      const stats = response.data;
      console.log("统计API响应:", stats);
      
      // 确保获取的是当前数据集的统计数据
      const counts = {
        annotated_count: stats.annotated_count || 0,
        total_count: stats.total_count || 0
      };
      
      console.log(`数据集${dataset.id}统计: 已标注${counts.annotated_count}张，总计${counts.total_count}张`);
      
      setAnnotatedCount(counts.annotated_count);
      setTotalCount(counts.total_count);
      setCountsCache(counts);
      setLastCountsUpdate(now);
    } catch (error) {
      console.error("获取统计信息失败:", error);
      // 重试机制：失败后3秒重试一次
      setTimeout(() => {
        if (dataset && user) {
          fetchCounts(true);
        }
      }, 3000);
    }
  };

  useEffect(() => {
    if (dataset && user && !imageIdInit) {
      fetchImage(imageId || null);
    }
    // 只依赖dataset和user，防止imageId导致循环
    // eslint-disable-next-line
  }, [dataset, user]);

  // 获取图片：
  // - 有 id：精准加载该图及其标注
  // - 无 id：优先取第一张未标注；若没有则用统计核验；若统计未完成再回退 next_image；仍无则视为完成
  const fetchImage = async (id) => {
    setIsLoading(true);
    setError(null);
    try {
      if (id) {
        // 获取所有图片及标注信息，找到 image_id === id 的那一张
        const { data } = await api.post('/images_with_annotations', {
          dataset_id: dataset.id,
          expert_id: user,
          role: role,
          include_all: true
        });
        const found = data.find(img => String(img.image_id) === String(id));
        if (found) {
          setImg(found);
          if (found.annotation) {
            setLabel(found.annotation.label !== undefined ? String(found.annotation.label) : '');
            setRemark(found.annotation.tip || '');
          } else {
            setLabel('');
            setRemark('');
          }
          setImageId(found.image_id);
          setImageScale(1);
          setImageOffset({ x: 0, y: 0 });
          setIsImageSelected(false);
          return;
        } else {
          console.warn(`找不到图片ID: ${id}`);
          // 如果找不到指定图片，继续下面的逻辑获取下一张
        }
      }
      
      // 获取所有图片及标注信息，优先显示未标注的图片
      const allImagesResponse = await api.post('/images_with_annotations', {
        dataset_id: dataset.id,
        expert_id: user,
        role: role,
        include_all: true
      });
      
      const allImages = allImagesResponse.data;
      console.log(`获取到数据集${dataset.id}的所有图片:`, allImages.length, '张');
      
      // 找到第一个未标注的图片
      const unAnnotatedImage = allImages.find(img => !img.annotation);
      
      if (unAnnotatedImage) {
        console.log(`找到未标注图片: ID ${unAnnotatedImage.image_id}`);
        setImg(unAnnotatedImage);
        setLabel('');
        setRemark('');
        setImageId(unAnnotatedImage.image_id);
        setImageScale(1);
        setImageOffset({ x: 0, y: 0 });
        setIsImageSelected(false);
      } else {
        // 获取统计信息再次确认
        try {
          const statsResponse = await api.get(`/datasets/${dataset.id}/statistics`, {
            params: { 
              expert_id: user, 
              role: role,
              dataset_id: dataset.id
            }
          });
          
          const stats = statsResponse.data;
          const annotatedCount = stats.annotated_count || 0;
          const totalCount = stats.total_count || 0;
          
          console.log(`统计信息确认: 已标注${annotatedCount}张，总计${totalCount}张`);
          
          if (annotatedCount >= totalCount && totalCount > 0) {
            // 确实全部标注完成
            console.log('确认所有图片已标注完成');
            setImg({ completed: true });
            setImageId(null);
          } else {
            // 统计数据显示还有未标注的，但获取不到图片，可能是数据不一致
            console.warn('数据不一致：统计显示有未标注图片，但找不到具体图片');
            
            // 尝试使用 /next_image 接口
            const nextImageResponse = await api.post('/next_image', {
              expert_id: user,
              dataset_id: dataset.id,
              role: role
            });
            
            if (nextImageResponse.data.image_id) {
              console.log(`通过next_image找到图片: ${nextImageResponse.data.image_id}`);
              setImg({ 
                image_id: nextImageResponse.data.image_id, 
                filename: nextImageResponse.data.filename 
              });
              setLabel('');
              setRemark('');
              setImageId(nextImageResponse.data.image_id);
              setImageScale(1);
              setImageOffset({ x: 0, y: 0 });
              setIsImageSelected(false);
            } else {
              // 如果还是找不到，显示完成状态
              console.log('next_image也没有返回图片，标注完成');
              setImg({ completed: true });
              setImageId(null);
            }
          }
        } catch (statsError) {
          console.error("获取统计信息失败:", statsError);
          // 如果统计接口失败，但我们从allImages中没找到未标注的图片，
          // 可能真的完成了，显示完成状态
          setImg({ completed: true });
          setImageId(null);
        }
      }
    } catch (error) {
      console.error("获取图片失败:", error);
      setError("加载图片失败，请重试");
      setImg(null);
    } finally {
      setIsLoading(false);
    }
  };

  // 提交标注：提交成功后按“未标注优先 -> 统计核验 -> next_image 回退 -> 完成”流程获取下一张
  const handleSubmit = async () => {
    if (!label) {
      console.warn("请选择标签");
      setError("请选择标签");
      return;
    }
    
    if (submitDisabled) {
      console.log("正在提交中，请勿重复点击");
      return;
    }
    
    setSubmitDisabled(true);
    setError(null);
    
    try {
      await api.post('/annotate', {
        expert_id: user,
        dataset_id: dataset.id,
        image_id: img.image_id,
        label,
        tip: remark
      });
      
      console.log(`标注提交成功: 图片${img.image_id}, 标签${label}`);
      setLabel('');
      setRemark('');
      
      // 提交后，重新获取图片（优先获取未标注的）
      try {
        // 获取所有图片及标注信息
        const allImagesResponse = await api.post('/images_with_annotations', {
          dataset_id: dataset.id,
          expert_id: user,
          role: role,
          include_all: true
        });
        
        const allImages = allImagesResponse.data;
        console.log(`提交后获取到所有图片: ${allImages.length}张`);
        
        // 找到第一个未标注的图片
        const unAnnotatedImage = allImages.find(img => !img.annotation);
        
        if (unAnnotatedImage) {
          console.log(`找到下一张未标注图片: ID ${unAnnotatedImage.image_id}`);
          setImg(unAnnotatedImage);
          setImageId(unAnnotatedImage.image_id);
          setImageScale(1);
          setImageOffset({ x: 0, y: 0 });
          setIsImageSelected(false);
        } else {
          // 没有找到未标注的图片，获取统计信息确认
          const statsResponse = await api.get(`/datasets/${dataset.id}/statistics`, {
            params: { 
              expert_id: user, 
              role: role,
              dataset_id: dataset.id
            }
          });
          
          const stats = statsResponse.data;
          const annotatedCount = stats.annotated_count || 0;
          const totalCount = stats.total_count || 0;
          
          console.log(`提交后统计: 已标注${annotatedCount}张，总计${totalCount}张`);
          
          if (annotatedCount >= totalCount && totalCount > 0) {
            // 确实全部标注完成
            console.log('提交后确认所有图片已标注完成');
            setImg({ completed: true });
            setImageId(null);
          } else {
            // 数据可能不一致，尝试使用next_image接口
            const nextImageResponse = await api.post('/next_image', {
              expert_id: user,
              dataset_id: dataset.id,
              role: role
            });
            
            if (nextImageResponse.data.image_id) {
              console.log(`通过next_image找到下一张图片: ${nextImageResponse.data.image_id}`);
              setImg({ 
                image_id: nextImageResponse.data.image_id, 
                filename: nextImageResponse.data.filename 
              });
              setImageId(nextImageResponse.data.image_id);
              setImageScale(1);
              setImageOffset({ x: 0, y: 0 });
              setIsImageSelected(false);
            } else {
              console.log('next_image也没有返回图片，标注完成');
              setImg({ completed: true });
              setImageId(null);
            }
          }
        }
      } catch (error) {
        console.error("获取下一张图片失败:", error);
        // 如果获取失败，回退到原来的fetchImage方法
        fetchImage();
      }
      
      fetchCounts(true); // 强制刷新计数
    } catch (error) {
      console.error("提交标注失败:", error);
      setError("提交失败，请重试");
      // 提示用户重试
      if (error.response?.status >= 500) {
        console.log("服务器错误，将在3秒后自动重试...");
        setTimeout(() => handleSubmit(), 3000);
      }
    } finally {
      // 延迟重新启用提交按钮，防止快速重复点击
      setTimeout(() => setSubmitDisabled(false), 1000);
    }
  };

  // 定义 handlePrev 函数
  const handlePrev = async () => { 
    try {
      const { data } = await api.post('/prev_image', {
        dataset_id: dataset.id,
        image_id: img.image_id
      });
      if (data.image_id) {
        fetchImage(data.image_id);
      } else {
        console.log("已经是第一张图片");
      }
    } catch (error) {
      console.error("获取上一张图片失败:", error);
      // 重试机制
      if (error.response?.status >= 500) {
        console.log("服务器错误，将在2秒后重试...");
        setTimeout(() => handlePrev(), 2000);
      }
    }
  };

  const handleImageMouseDown = (e) => {
    // 单击选中图片
    setIsImageSelected(true);
    
    if (imageScale > 1) {
      e.preventDefault();
      setIsDragging(true);
      setDragStart({ x: e.clientX - imageOffset.x, y: e.clientY - imageOffset.y });
    }
  };

  const handleImageMouseMove = (e) => {
    if (isDragging && imageScale > 1) {
      e.preventDefault();
      const newX = e.clientX - dragStart.x;
      const newY = e.clientY - dragStart.y;

      // 计算图片容器的边界限制
      const container = e.target.parentElement;
      const containerRect = container.getBoundingClientRect();
      const imgRect = e.target.getBoundingClientRect();

      // 计算缩放后图片的实际尺寸
      const scaledWidth = imgRect.width;
      const scaledHeight = imgRect.height;
      const containerWidth = containerRect.width;
      const containerHeight = containerRect.height;

      // 计算允许的最大偏移量（防止图片完全移出可视区域）
      const maxOffsetX = Math.max(0, (scaledWidth - containerWidth) / 2);
      const maxOffsetY = Math.max(0, (scaledHeight - containerHeight) / 2);

      // 限制偏移范围
      const constrainedX = Math.max(-maxOffsetX, Math.min(maxOffsetX, newX));
      const constrainedY = Math.max(-maxOffsetY, Math.min(maxOffsetY, newY));
      

      setImageOffset( { x: constrainedX, y: constrainedY } );
    }
  };

  // 处理拖拽开始事件，阻止浏览器默认拖拽
  const handleImageDragStart = (e) => {
    e.preventDefault();
    return false;
  };

  // 处理右键菜单，阻止浏览器默认右键菜单
  const handleImageContextMenu = (e) => {
    e.preventDefault();
    return false;
  };

  const handleImageMouseUp = () => {
    setIsDragging(false);
  };

  const resetImageView = () => {
    setImageScale(1);
    setImageOffset({ x: 0, y: 0 });
    setIsImageSelected(false); // 重置时取消选中状态
  };

  // 点击图片外部区域取消选中
  const handleContainerClick = (e) => {
    if (e.target === e.currentTarget) {
      setIsImageSelected(false);
    }
  };

  if (isLoading) return (
    <div className="loading-box">
      <div className="loading-spinner"></div>
      <p>正在加载图片...</p>
    </div>
  );
  
  if (error) return (
    <div className="error-box">
      <p className="error-message">❌ {error}</p>
      <button className="btn" onClick={() => {
        setError(null);
        fetchImage(imageId);
      }}>重试</button>
      <button className="btn secondary" onClick={onDone}>返回</button>
    </div>
  );

  if (!img) return <div className="done-box">标注完成！<button className="btn" onClick={onDone}>返回</button></div>;
  if (img.completed) return (
    <div className="completion-overlay">
      <div className="completion-card">
        <div className="completion-icon">🎉</div>
        <h2 className="completion-title">恭喜！</h2>
        <p className="completion-message">本数据集已全部标注完成</p>
        <div className="completion-stats">
          <span className="completion-stat">
            <strong>{annotatedCount}</strong> 张图片已完成标注
          </span>
        </div>
        <div className="completion-actions">
          <button className="btn completion-btn secondary" onClick={() => onSelectMode && onSelectMode()}>继续查看本数据集</button>
          <button className="btn completion-btn" onClick={onDone}>返回数据集选择</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="annotate-box">
      <div className="progress-section">
        <div className="progress-info">
          <div className="progress-text-card">
            <div className="progress-stats">
              <div className="stat-item completed">
                <span className="stat-number">{annotatedCount}</span>
                <span className="stat-label">已标注</span>
              </div>
              <div className="stat-divider">|</div>
              <div className="stat-item remaining">
                <span className="stat-number">{Math.max(0, totalCount - annotatedCount)}</span>
                <span className="stat-label">剩余</span>
              </div>
              <div className="stat-divider">|</div>
              <div className="stat-item total">
                <span className="stat-number">{totalCount}</span>
                <span className="stat-label">总计</span>
              </div>
            </div>
          </div>
        </div>
        <div className="progress-visual">
          <div className="progress-circle">
            <svg width="90" height="90" viewBox="0 0 90 90">
              <circle
                cx="45"
                cy="45"
                r="35"
                fill="none"
                stroke="#e0e7ff"
                strokeWidth="8"
              />
              <circle
                cx="45"
                cy="45"
                r="35"
                fill="none"
                stroke="url(#progressGradient)"
                strokeWidth="8"
                strokeDasharray={`${2 * Math.PI * 35}`}
                strokeDashoffset={`${2 * Math.PI * 35 * (1 - (totalCount > 0 ? annotatedCount / totalCount : 0))}`}
                transform="rotate(-90 45 45)"
                style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#1677ff" />
                  <stop offset="100%" stopColor="#4f8cff" />
                </linearGradient>
              </defs>
            </svg>
            <div className="progress-percentage">
              {totalCount > 0 ? Math.round((annotatedCount / totalCount) * 100) : 0}%
            </div>
          </div>
        </div>
      </div>
      <h2>标注图片: ID #{img.image_id}</h2>
      {img && (
        <div className="image-container" onClick={handleContainerClick}>
          <div 
            className={`image-viewer ${isImageSelected ? 'selected' : ''}`}
            onMouseDown={handleImageMouseDown}
            onMouseMove={handleImageMouseMove}
            onMouseUp={handleImageMouseUp}
            onMouseEnter={() => setIsImageHovered(true)}
            onMouseLeave={() => {
              setIsImageHovered(false);
              handleImageMouseUp();
            }}
          >
            <img 
              src={`/static/img/${img.filename}`} 
              alt={`图片ID: ${img.image_id}`}
              loading="lazy"
              onError={(e) => {
                console.error(`图片加载失败: ${img.filename}`);
                e.target.src = '/placeholder-error.png'; // 可以添加一个错误占位图
              }}
              onLoad={() => {
                console.log(`图片加载成功: ${img.filename}`);
              }}
              style={{ 
                transform: `scale(${imageScale}) translate(${imageOffset.x / imageScale}px, ${imageOffset.y / imageScale}px)`,
                cursor: imageScale > 1 ? (isDragging ? 'grabbing' : 'grab') : (isImageSelected ? 'zoom-in' : 'pointer'),
                transition: isDragging ? 'none' : 'transform 0.1s ease',
                userSelect: 'none',
                pointerEvents: 'auto',
              }} 
              onDragStart={handleImageDragStart} // 阻止拖拽开始
              onContextMenu={handleImageContextMenu} // 阻止右键菜单
              draggable={false} // 禁用HTML5拖拽
            />
          </div>
          <div className="image-controls">
            <div className="control-buttons">
              <button className="control-btn" onClick={() => setImageScale(prev => Math.max(0.3, prev - 0.2))}>-</button>
              <span className="scale-text">{Math.round(imageScale * 100)}%</span>
              <button className="control-btn" onClick={() => setImageScale(prev => Math.min(3, prev + 0.2))}>+</button>
              <button className="control-btn reset-btn" onClick={resetImageView}>重置</button>
            </div>
          </div>
          <div className="img-id">图片 ID: #{img.image_id}</div>
        </div>
      )}
      <div className="form-row label-row">
        <label>标签：</label>
        <div className="label-btn-group">
          {labels.length === 0 ? (
            <div style={{color: '#999', fontSize: '14px', padding: '10px'}}>
              {error || "正在加载标签..."}
            </div>
          ) : (
            labels.map(l => {
              console.log("渲染标签按钮:", l);
              // 确保类型一致性，都转为字符串再比较
              const isSelected = String(label) === String(l.label_id || l.id);
              return (
                <button
                  key={l.label_id || l.id}
                  type="button"
                  className={"label-btn" + (isSelected ? " selected" : "")}
                  onClick={() => {
                    const labelId = l.label_id || l.id;
                    console.log(`选择标签: ${l.name}, ID: ${labelId}`);
                    setLabel(String(labelId)); // 统一转为字符串
                    setError(null); // 清除错误信息
                  }}
                >{l.name}</button>
              );
            })
          )}
        </div>
      </div>
      <div className="form-row">
        <label>备注：</label>
        <input className="input" value={remark} onChange={e => setRemark(e.target.value)} placeholder="可选" />
      </div>
      <button 
        className="btn" 
        onClick={handleSubmit} 
        disabled={!label || submitDisabled}
        style={{ opacity: submitDisabled ? 0.6 : 1 }}
      >
        {submitDisabled ? "提交中..." : "提交并下一张"}
      </button>
      <button className="btn" onClick={handlePrev} style={{ marginLeft: 12 }}>上一张</button>
    </div>
  );
}

function ImageSelector({ user, dataset, role, onSelect, onBack, pageSize = 20 }) {
  const [images, setImages] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    setImages([]); // 重置图片列表
    setPage(1);
    setHasMore(true);
    loadImages(1, true); // 加载第一页
  }, [dataset, user]);

  const loadImages = async (pageNum = page, reset = false) => {
    setLoading(true);
    try {
      // 获取所有图片（包括已标注和未标注的）
      const { data } = await api.post('/images_with_annotations', {
        dataset_id: dataset.id,
        expert_id: user,
        role: role, // 添加角色信息
        page: pageNum,
        pageSize,
        include_all: true // 包含所有图片，不只是未标注的
      });
      
      if (reset) {
        setImages(data);
      } else {
        setImages(prev => [...prev, ...data]);
      }
      
      setHasMore(data.length === pageSize);
    } catch (error) {
      console.error("加载图片失败:", error);
      // 如果API不支持include_all参数，尝试使用旧的方式
      try {
        const { data } = await api.get(`/datasets/${dataset.id}/images`, {
          params: {
            expert_id: user,
            role: role,
            page: pageNum,
            pageSize
          }
        });
        
        if (reset) {
          setImages(data);
        } else {
          setImages(prev => [...prev, ...data]);
        }
        
        setHasMore(data.length === pageSize);
      } catch (fallbackError) {
        console.error("备用加载图片方式也失败:", fallbackError);
        setImages([]);
        setHasMore(false);
      }
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
        {images.map(img=>(
          <div key={img.image_id} className="image-selector-item">
            <img 
              src={`/static/img/${img.filename}`} 
              alt={`图片ID: ${img.image_id}`} 
              className="image-selector-thumb"
              loading="lazy"
              onError={(e) => {
                console.error(`缩略图加载失败: ${img.filename}`);
                e.target.style.display = 'none'; // 隐藏加载失败的图片
              }}
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
            <button className="btn" onClick={()=>onSelect(img.image_id)}>
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
          <button className="btn" onClick={handleLoadMore} style={{width:'100%',marginTop:16}}>
            加载更多
          </button>
        )}
      </div>
    </div>
  );
}

function Export({ dataset, user, role }) {
  const [exporting, setExporting] = useState(false);
  
  const handleExport = () => {
    setExporting(true);
    
    // 构建导出URL，添加数据集和用户筛选参数
    let exportUrl = '/api/export';
    const params = [];
    
    if (dataset && dataset.id) {
      params.push(`dataset_id=${dataset.id}`);
    }
    
    if (user) {
      params.push(`expert_id=${user}`);
    }
    
    if (params.length > 0) {
      exportUrl += '?' + params.join('&');
    }
    
    // 打开导出URL
    window.open(exportUrl, '_blank');
    
    // 短暂延迟后重置状态
    setTimeout(() => {
      setExporting(false);
    }, 2000);
  };
  
  return (
    <button 
      className={`btn ${exporting ? 'exporting' : ''}`} 
      onClick={handleExport}
      disabled={exporting}
    >
      {exporting ? '导出中...' : '导出Excel'}
    </button>
  );
}

// 数据集管理组件
function DatasetManager({ user, role, onBack }) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [showLabelManager, setShowLabelManager] = useState(false);
  const [showUserManager, setShowUserManager] = useState(false);
  const [editingDatasetId, setEditingDatasetId] = useState(null);
  const [datasetLabels, setDatasetLabels] = useState([]);
  
  // 表单数据
  const [newDatasetName, setNewDatasetName] = useState('');
  const [newDatasetDesc, setNewDatasetDesc] = useState('');
  const [labelInputs, setLabelInputs] = useState([{ name: '', category: '病理学' }]);
  const [files, setFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  useEffect(() => {
    fetchDatasets();
  }, []);
  
  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const response = await api.get('/datasets');
      setDatasets(response.data || []);
    } catch (error) {
      console.error('获取数据集失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取数据集标签
  const fetchDatasetLabels = async (datasetId) => {
    try {
      const response = await api.get(`/admin/datasets/${datasetId}/labels?role=${role}`);
      const labels = response.data.map(label => ({
        name: label.label_name,
        category: label.category || '病理学'
      }));
      setDatasetLabels(labels.length > 0 ? labels : [{ name: '', category: '病理学' }]);
    } catch (error) {
      console.error('获取数据集标签失败:', error);
      setDatasetLabels([{ name: '', category: '病理学' }]);
    }
  };
  
  const handleCreateDataset = async () => {
    if (!newDatasetName.trim()) {
      alert('请输入数据集名称');
      return;
    }
    
    try {
      const response = await api.post('/admin/datasets', {
        name: newDatasetName,
        description: newDatasetDesc,
        role: role
      });
      
      if (response.data.msg === 'success') {
        // 创建成功后添加标签
        if (labelInputs.length > 0) {
          const validLabels = labelInputs.filter(label => label.name.trim() !== '');
          if (validLabels.length > 0) {
            await api.post(`/admin/datasets/${response.data.dataset_id}/labels`, {
              labels: validLabels,
              role: role
            });
          }
        }
        
        alert('数据集创建成功!');
        setNewDatasetName('');
        setNewDatasetDesc('');
        setLabelInputs([{ name: '', category: '病理学' }]);
        setShowCreateForm(false);
        fetchDatasets(); // 刷新数据集列表
      }
    } catch (error) {
      console.error('创建数据集失败:', error);
      alert(`创建失败: ${error.response?.data?.error || error.message}`);
    }
  };
  
  const handleDeleteDataset = async (datasetId) => {
    if (!window.confirm('确认删除此数据集? 此操作不可恢复!')) {
      return;
    }
    
    try {
      const response = await api.delete(`/admin/datasets/${datasetId}?role=${role}`);
      if (response.data.msg === 'success') {
        alert('数据集删除成功!');
        fetchDatasets(); // 刷新数据集列表
      }
    } catch (error) {
      console.error('删除数据集失败:', error);
      alert(`删除失败: ${error.response?.data?.error || error.message}`);
    }
  };
  
  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };
  
  const handleUpload = async () => {
    if (!selectedDataset) {
      alert('请先选择数据集');
      return;
    }
    
    if (!files.length) {
      alert('请选择至少一张图片');
      return;
    }
    
    const formData = new FormData();
    formData.append('role', role);
    
    files.forEach(file => {
      formData.append('images', file);
    });
    
    try {
      const response = await api.post(`/admin/datasets/${selectedDataset.id}/images`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });
      
      if (response.data.msg === 'success') {
        alert(`上传成功! 成功上传 ${response.data.uploaded} 张图片, 失败 ${response.data.failed} 张`);
        setFiles([]);
        setUploadProgress(0);
        setShowUploadForm(false);
        fetchDatasets(); // 刷新数据集列表
      }
    } catch (error) {
      console.error('上传图片失败:', error);
      alert(`上传失败: ${error.response?.data?.error || error.message}`);
    }
  };
  
  const addLabelInput = () => {
    setLabelInputs([...labelInputs, { name: '', category: '病理学' }]);
  };
  
  const updateLabelInput = (index, field, value) => {
    const updatedInputs = [...labelInputs];
    updatedInputs[index][field] = value;
    setLabelInputs(updatedInputs);
  };
  
  const removeLabelInput = (index) => {
    const updatedInputs = [...labelInputs];
    updatedInputs.splice(index, 1);
    setLabelInputs(updatedInputs);
  };
  
  return (
    <div className="dataset-card" style={{maxWidth: 800}}>
      <div className="selector-header">
        <h2>数据集管理面板</h2>
        <button className="btn back-btn" onClick={onBack}>返回</button>
      </div>
      
      <div className="admin-controls">
        <button 
          className="btn admin-btn" 
          onClick={() => {
            setShowCreateForm(true);
            setShowUploadForm(false);
            setShowUserManager(false);
          }}
        >
          创建新数据集
        </button>
        
        <button 
          className="btn admin-btn" 
          onClick={() => {
            setShowUploadForm(true);
            setShowCreateForm(false);
            setShowUserManager(false);
          }}
          disabled={datasets.length === 0}
        >
          上传图片
        </button>
        
        <button 
          className="btn admin-btn" 
          onClick={() => {
            setShowUserManager(true);
            setShowCreateForm(false);
            setShowUploadForm(false);
          }}
        >
          用户管理
        </button>
      </div>
      
      {showCreateForm && (
        <div className="form-container">
          <h3>创建新数据集</h3>
          <div className="form-row">
            <label>数据集名称:</label>
            <input 
              className="input" 
              value={newDatasetName} 
              onChange={e => setNewDatasetName(e.target.value)}
              placeholder="例如: 肺炎CT图像集"
            />
          </div>
          
          <div className="form-row">
            <label>数据集描述:</label>
            <textarea 
              className="input" 
              value={newDatasetDesc} 
              onChange={e => setNewDatasetDesc(e.target.value)}
              placeholder="描述该数据集的用途和内容"
              style={{minHeight: 80}}
            />
          </div>
          
          <div className="label-section">
            <h3>标签配置</h3>
            <p className="hint-text">添加该数据集的标签选项，标注时将使用这些标签</p>
            
            {labelInputs.map((label, index) => (
              <div key={index} className="label-input-row">
                <input 
                  className="input label-name-input" 
                  value={label.name} 
                  onChange={e => updateLabelInput(index, 'name', e.target.value)}
                  placeholder="标签名称"
                />
                <select 
                  className="select" 
                  value={label.category} 
                  onChange={e => updateLabelInput(index, 'category', e.target.value)}
                >
                  <option value="病理学">病理学</option>
                  <option value="解剖学">解剖学</option>
                  <option value="影像学">影像学</option>
                </select>
                <button 
                  className="btn-icon remove-btn" 
                  onClick={() => removeLabelInput(index)}
                  title="移除此标签"
                >
                  ×
                </button>
              </div>
            ))}
            
            <button className="btn-text" onClick={addLabelInput}>+ 添加标签</button>
          </div>
          
          <div className="form-actions">
            <button className="btn cancel-btn" onClick={() => setShowCreateForm(false)}>取消</button>
            <button className="btn" onClick={handleCreateDataset}>创建数据集</button>
          </div>
        </div>
      )}
      
      {showUploadForm && (
        <div className="form-container">
          <h3>上传图片</h3>
          <div className="form-row">
            <label>选择数据集:</label>
            <select 
              className="select" 
              value={selectedDataset ? selectedDataset.id : ''} 
              onChange={e => {
                const id = parseInt(e.target.value);
                const dataset = datasets.find(d => d.id === id);
                setSelectedDataset(dataset);
              }}
            >
              <option value="">-- 选择数据集 --</option>
              {datasets.map(ds => (
                <option key={ds.id} value={ds.id}>{ds.name}</option>
              ))}
            </select>
          </div>
          
          <div className="form-row">
            <label>选择图片:</label>
            <input 
              type="file" 
              multiple 
              accept="image/*" 
              onChange={handleFileChange}
              className="file-input"
            />
            <p className="hint-text">支持jpg, png, jpeg等图片格式，可多选</p>
          </div>
          
          {files.length > 0 && (
            <div className="file-preview">
              <p>已选择 {files.length} 个文件</p>
              <ul className="file-list">
                {files.slice(0, 5).map((file, i) => (
                  <li key={i}>{file.name} ({(file.size / 1024).toFixed(1)} KB)</li>
                ))}
                {files.length > 5 && <li>...等 {files.length - 5} 个文件</li>}
              </ul>
            </div>
          )}
          
          {uploadProgress > 0 && (
            <div className="progress-bar-container">
              <div 
                className="progress-bar" 
                style={{width: `${uploadProgress}%`}}
              />
              <span className="progress-text">{uploadProgress}%</span>
            </div>
          )}
          
          <div className="form-actions">
            <button className="btn cancel-btn" onClick={() => setShowUploadForm(false)}>取消</button>
            <button 
              className="btn" 
              onClick={handleUpload}
              disabled={!selectedDataset || files.length === 0}
            >
              上传图片
            </button>
          </div>
        </div>
      )}
      
      {showLabelManager && (
        <div className="form-container">
          <h3>管理数据集 #{editingDatasetId} 标签</h3>
          <div className="label-section">
            {datasetLabels.map((label, index) => (
              <div key={index} className="label-input-row">
                <input 
                  className="input label-name-input" 
                  value={label.name} 
                  onChange={e => {
                    const updated = [...datasetLabels];
                    updated[index].name = e.target.value;
                    setDatasetLabels(updated);
                  }}
                  placeholder="标签名称"
                />
                <select 
                  className="select" 
                  value={label.category} 
                  onChange={e => {
                    const updated = [...datasetLabels];
                    updated[index].category = e.target.value;
                    setDatasetLabels(updated);
                  }}
                >
                  <option value="病理学">病理学</option>
                  <option value="解剖学">解剖学</option>
                  <option value="影像学">影像学</option>
                </select>
                <button 
                  className="btn-icon remove-btn" 
                  onClick={() => {
                    const updated = [...datasetLabels];
                    updated.splice(index, 1);
                    setDatasetLabels(updated);
                  }}
                  title="移除此标签"
                >
                  ×
                </button>
              </div>
            ))}
            
            <button className="btn-text" onClick={() => 
              setDatasetLabels([...datasetLabels, { name: '', category: '病理学' }])
            }>
              + 添加标签
            </button>
          </div>
          
          <div className="form-actions">
            <button className="btn cancel-btn" onClick={() => setShowLabelManager(false)}>取消</button>
            <button 
              className="btn" 
              onClick={async () => {
                try {
                  const validLabels = datasetLabels.filter(l => l.name.trim() !== '');
                  const response = await api.put(`/admin/datasets/${editingDatasetId}/labels`, {
                    labels: validLabels,
                    role: role
                  });
                  if(response.data.msg === 'success') {
                    alert('标签更新成功!');
                    setShowLabelManager(false);
                  }
                } catch (error) {
                  console.error('更新标签失败:', error);
                  alert(`更新失败: ${error.response?.data?.error || error.message}`);
                }
              }}
            >
              保存标签
            </button>
          </div>
        </div>
      )}
      
      {showUserManager && <UserManager role={role} />}
      
      <div className="datasets-list">
        <h3>现有数据集</h3>
        {loading ? (
          <div className="loading-text">加载数据集...</div>
        ) : datasets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-title">暂无数据集</div>
            <div className="empty-subtitle">点击"创建新数据集"按钮创建您的第一个数据集</div>
          </div>
        ) : (
          <div className="dataset-table">
            <div className="dataset-table-header">
              <div className="col-id">ID</div>
              <div className="col-name">名称</div>
              <div className="col-count">图片数量</div>
              <div className="col-actions">操作</div>
            </div>
            
            {datasets.map(dataset => (
              <div key={dataset.id} className="dataset-table-row">
                <div className="col-id">{dataset.id}</div>
                <div className="col-name">{dataset.name}</div>
                <div className="col-count">{dataset.image_count || 0}</div>
                <div className="col-actions">
                  <button 
                    className="btn-text manage-btn" 
                    onClick={() => {
                      setEditingDatasetId(dataset.id);
                      fetchDatasetLabels(dataset.id);
                      setShowLabelManager(true);
                    }}
                  >
                    管理标签
                  </button>
                  <button 
                    className="btn-text fix-btn" 
                    onClick={async () => {
                      try {
                        const response = await api.post(`/admin/datasets/${dataset.id}/recount`, {
                          role: role
                        });
                        if(response.data.msg === 'success') {
                          alert(`图片数量已更新为: ${response.data.image_count}`);
                          fetchDatasets(); // 刷新数据集列表
                        }
                      } catch (error) {
                        console.error('修正图片数量失败:', error);
                        alert(`修正失败: ${error.response?.data?.error || error.message}`);
                      }
                    }}
                  >
                  修正统计
                  </button>
                  <button 
                    className="btn-text delete-btn" 
                    onClick={() => handleDeleteDataset(dataset.id)}
                  >
                  删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function UserManager({ role }) {
  const [users, setUsers] = useState([]);
  const [configInfo, setConfigInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
    fetchConfigInfo();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await api.get(`/admin/users?role=${role}`);
      setUsers(response.data || []);
    } catch (error) {
      console.error('获取用户列表失败:', error);
      setUsers([]);
    }
  };

  const fetchConfigInfo = async () => {
    try {
      const response = await api.get(`/admin/users/config?role=${role}`);
      setConfigInfo(response.data);
    } catch (error) {
      console.error('获取配置信息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="form-container">
        <h3>用户管理</h3>
        <div className="loading-text">加载用户信息...</div>
      </div>
    );
  }

  return (
    <div className="form-container">
      <h3>用户管理</h3>
      
      {configInfo && (
        <div className="config-info">
          <div className="info-title">📝 用户管理说明</div>
          <div className="info-content">
            <p><strong>管理方式：</strong>{configInfo.message}</p>
            <p><strong>配置文件：</strong><code>{configInfo.config_file}</code></p>
            <div className="instructions">
              <strong>操作步骤：</strong>
              <ol>
                {configInfo.instructions.map((instruction, index) => (
                  <li key={index}>{instruction}</li>
                ))}
              </ol>
            </div>
            <div className="stats">
              <span>当前用户数量: <strong>{configInfo.current_users_count}</strong></span>
              <span>角色映射: {Object.entries(configInfo.roles_mapping).map(([role, id]) => 
                `${role}(${id})`
              ).join(', ')}</span>
            </div>
          </div>
        </div>
      )}

      <div className="users-list">
        <h4>当前系统用户</h4>
        {users.length === 0 ? (
          <div className="empty-state">
            <div className="empty-title">无法获取用户信息</div>
            <div className="empty-subtitle">请检查权限或联系系统管理员</div>
          </div>
        ) : (
          <div className="user-table">
            <div className="user-table-header">
              <div className="col-username">用户名</div>
              <div className="col-role">角色</div>
              <div className="col-description">描述</div>
            </div>
            
            {users.map((user, index) => (
              <div key={index} className="user-table-row">
                <div className="col-username">{user.username}</div>
                <div className="col-role">
                  <span className={`role-badge role-${user.role}`}>
                    {user.role === 'admin' ? '管理员' : 
                     user.role === 'doctor' ? '医生' : '学生'}
                  </span>
                </div>
                <div className="col-description">{user.description}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const style = document.createElement('style');
style.innerHTML = `
body {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
  font-family: 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
  letter-spacing: 0.02em;
  line-height: 1.6;
  color: #2c3e50;
  font-weight: 400;
}
  .app-container {
  position: relative;
  min-height: 100vh;
}

.page-logos {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.logo-left {
  position: absolute;
  top: 50px;
  left: 60px;
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  padding: 15px;
  border-radius: 25px;
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: auto;
  transition: transform 0.4s ease, box-shadow 0.4s ease;
  transform: rotate(-5deg);
}

.logo-right {
  position: absolute;
  top: 50px;
  right: 60px;
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  padding: 15px;
  border-radius: 25px;
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: auto;
  transition: transform 0.4s ease, box-shadow 0.4s ease;
  transform: rotate(5deg);
}

.logo-left:hover {
  transform: rotate(5deg) scale(1.1);
  box-shadow: 0 12px 35px rgba(52, 152, 219, 0.6);
}

.logo-right:hover {
  transform: rotate(-5deg) scale(1.1);
  box-shadow: 0 12px 35px rgba(52, 152, 219, 0.6);
}

.page-logo {
  width: 140px;
  height: 140px;
  object-fit: contain;
  border-radius: 16px;
}

.main-bg {
  position: relative;
  z-index: 2;
  max-width: 720px;
  margin: 64px auto 0 auto;
  background: rgba(255,255,255,0.98);
  border-radius: 28px;
  box-shadow: 0 8px 48px #8ec5fc44;
  padding: 56px 56px 40px 56px;
  min-height: 520px;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 36px;
  border-bottom: 1.5px solid #e6e6e6;
  padding-bottom: 16px;
  font-size: 17px;
  position: relative;
  font-weight: 500;
  color: #34495e;
}
.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-placeholder {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  border: 2px solid #1677ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #1677ff;
  font-weight: 600;
  text-align: center;
  line-height: 1.1;
}
.btn {
  background: linear-gradient(90deg, #4f8cff 0%, #1677ff 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 13px 38px;
  font-size: 18px;
  cursor: pointer;
  margin-left: 10px;
  margin-top: 8px;
  transition: background 0.2s, box-shadow 0.2s, transform 0.1s;
  box-shadow: 0 2px 12px #1677ff22;
  font-weight: 500;
}
.btn:hover:not(:disabled) {
  background: linear-gradient(90deg, #1677ff 0%, #4f8cff 100%);
  transform: translateY(-2px) scale(1.04);
  box-shadow: 0 4px 18px #1677ff33;
}
.btn:disabled {
  background: #bfc7d1;
  cursor: not-allowed;
  box-shadow: none;
}
.btn.logout {
  background: linear-gradient(90deg, #ff4d4f 0%, #f5222d 100%);
}
.btn.logout:hover:not(:disabled) {
  background: linear-gradient(90deg, #f5222d 0%, #ff4d4f 100%);
}
.form-row {
  margin: 28px 0;
  display: flex;
  align-items: center;
}
.form-row.label-row { align-items: flex-start; }
.form-row label {
  width: 90px;
  color: #2c3e50;
  font-weight: 600;
  letter-spacing: 0.5px;
  font-size: 16px;
  margin-top: 8px;
  line-height: 1.5;
}
.select, .input {
  flex: 1;
  padding: 13px 16px;
  border: 1.5px solid #bfc7d1;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
  transition: border 0.2s, box-shadow 0.2s;
  font-family: inherit;
  color: #2c3e50;
  line-height: 1.5;
}
.select:focus, .input:focus {
  border: 1.5px solid #1677ff;
  background: #fff;
  box-shadow: 0 0 0 2px #1677ff22;
}
.label-btn-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.label-btn {
  background: linear-gradient(90deg, #f0f4ff 0%, #e6f0ff 100%);
  color: #1677ff;
  border: 2px solid #d1e0ff;
  border-radius: 18px;
  padding: 12px 32px;
  font-size: 17px;
  margin: 4px 0;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px #8ec5fc33;
  transition: all 0.2s ease;
}
.label-btn.selected {
  background: linear-gradient(90deg, #1677ff 0%, #0d4f8c 100%);
  color: #fff;
  border-color: #0d4f8c;
  box-shadow: 0 4px 16px rgba(22, 119, 255, 0.56);
  transform: scale(1.06);
}
.label-btn:hover:not(.selected) {
  background: linear-gradient(90deg, #e6f0ff 0%, #bdd4ff 100%);
  border-color: #1677ff;
  box-shadow: 0 4px 12px #1677ffa2;
  transform: scale(1.03);
}
.img-name {
  color: #1677ff;
  font-weight: bold;
  font-size: 22px;
}
.img-id {
  color: #1677ff;
  font-weight: 600;
  font-size: 17px;
  text-align: center;
  margin-top: 12px;
  letter-spacing: 0.3px;
}
.progress-section {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #e2e8f0;
}
.progress-info {
  flex: 1;
}
.progress-text-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
}
.progress-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.stat-number {
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
}
.stat-label {
  font-size: 14px;
  font-weight: 600;
  margin-top: 4px;
  color: #6b7280;
  letter-spacing: 0.3px;
}
.stat-item.completed .stat-number { color: #059669; }
.stat-item.remaining .stat-number { color: #dc2626; }
.stat-item.total .stat-number { color: #1677ff; }
.stat-divider {
  color: #9ca3af;
  font-size: 18px;
}
.progress-visual {
  display: flex;
  align-items: center;
  justify-content: center;
}
.progress-circle {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.progress-percentage {
  position: absolute;
  font-size: 17px;
  font-weight: 700;
  color: #1677ff;
}
.progress-text {
  color: #0369a1;
  font-size: 16px;
  font-weight: 500;
}
.image-container {
  text-align: center;
  margin-bottom: 20px;
}
.image-viewer {
  display: inline-block;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 2px 16px rgba(0,0,0,0.1);
  max-width: 90%;
  max-height: 400px;
  position: relative;
  background: #f8f9fa;
  user-select: none; /* 禁止选择 */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  border: 3px solid transparent;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.image-viewer.selected {
  border-color: #1677ff;
  box-shadow: 0 2px 16px rgba(0,0,0,0.1), 0 0 0 2px rgba(22, 119, 255, 0.2);
}
.image-viewer img {
  max-width: 100%;
  max-height: 400px;
  display: block;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  -webkit-user-drag: none; /* Safari 禁用拖拽 */
  -khtml-user-drag: none;
  -moz-user-drag: none;
  -o-user-drag: none;
  user-drag: none;
  pointer-events: auto;
}
.image-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}
.control-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.control-btn {
  background: #f8f9fa;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.control-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}
.reset-btn {
  background: #1677ff;
  color: white;
  border-color: #1677ff;
}
.reset-btn:hover {
  background: #0d4f8c;
  border-color: #0d4f8c;
}
.scale-text {
  font-size: 15px;
  color: #4b5563;
  min-width: 50px;
  text-align: center;
  font-weight: 600;
}
.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 20px;
}
.back-btn {
  background: linear-gradient(90deg, #6b7280 0%, #4b5563 100%);
  padding: 10px 18px;
  font-size: 15px;
  font-weight: 600;
}
.back-btn:hover {
  background: linear-gradient(90deg, #4b5563 0%, #374151 100%);
}
.done-box {
  text-align: center;
  margin: 100px 0;
  font-size: 22px;
  color: #1677ff;
}

.loading-box {
  text-align: center;
  margin: 100px 0;
  font-size: 18px;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-box {
  text-align: center;
  margin: 100px 0;
  padding: 20px;
}

.error-message {
  font-size: 18px;
  color: #dc3545;
  margin-bottom: 20px;
}

.btn.secondary {
  background: #6c757d;
  color: white;
  margin-left: 10px;
}

.btn.secondary:hover {
  background: #5a6268;
}
.completion-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.completion-card {
  background: white;
  border-radius: 24px;
  padding: 48px 40px;
  text-align: center;
  max-width: 450px;
  margin: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: completionSlideIn 0.4s ease-out;
}
@keyframes completionSlideIn {
  from {
    opacity: 0;
    transform: scale(0.8) translateY(-30px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
.completion-icon {
  font-size: 64px;
  margin-bottom: 20px;
  animation: completionBounce 1s ease-in-out infinite alternate;
}
@keyframes completionBounce {
  from { transform: translateY(0); }
  to { transform: translateY(-10px); }
}
.completion-title {
  color: #1677ff;
  font-size: 32px;
  margin-bottom: 16px;
  font-weight: 700;
}
.completion-message {
  color: #5a6c7d;
  font-size: 18px;
  margin-bottom: 24px;
  line-height: 1.6;
  font-weight: 400;
}
.completion-stats {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 32px;
  border: 1px solid #bae6fd;
}
.completion-stat {
  color: #0369a1;
  font-size: 16px;
  font-weight: 500;
}
.completion-stat strong {
  color: #1677ff;
  font-size: 24px;
  font-weight: 700;
}
.completion-btn {
  background: linear-gradient(90deg, #059669 0%, #047857 100%);
  font-size: 18px;
  padding: 16px 32px;
  margin: 0 8px;
}
.completion-btn:hover {
  background: linear-gradient(90deg, #047857 0%, #059669 100%);
}
.completion-btn.secondary {
  background: linear-gradient(90deg, #6b7280 0%, #4b5563 100%);
}
.completion-btn.secondary:hover {
  background: linear-gradient(90deg, #4b5563 0%, #374151 100%);
}
.completion-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}
.export-bar {
  margin-top: 48px;
  text-align: right;
}
.login-bg, .select-bg {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
}
.login-card {
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 4px 32px #8ec5fc44;
  padding: 48px 40px 32px 40px;
  min-width: 450px;
  max-width: 75vw; /* 占页面3/4的宽度 */
  display: flex;
  flex-direction: column;
  align-items: center;
}
.dataset-card {
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 4px 32px #8ec5fc44;
  padding: 48px 40px 32px 40px;
  min-width: 450px;
  max-width: 75vw; /* 占页面3/4的宽度 */
  display: flex;
  flex-direction: column;
  align-items: center;
}
.dataset-btn-group {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
  margin-top: 18px;
}
.dataset-btn {
  background: linear-gradient(90deg, #e0e7ff 0%, #8ec5fc 100%);
  color: #1677ff;
  border: none;
  border-radius: 18px;
  padding: 18px 0;
  font-size: 20px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px #8ec5fc33;
  transition: background 0.2s, color 0.2s, box-shadow 0.2s, transform 0.1s;
  width: 100%;
  outline: none;
}
.dataset-btn:hover, .dataset-btn:focus {
  background: linear-gradient(90deg, #4f8cff 0%, #1677ff 100%);
  color: #fff;
  box-shadow: 0 4px 16px #1677ff33;
  transform: scale(1.03);
}
.login-btn { margin-top: 10px; }
.login-msg { 
  color: #e74c3c; 
  min-height: 24px; 
  font-size: 16px; 
  font-weight: 500;
  line-height: 1.5;
}
.login-tip { 
  color: #7f8c8d; 
  font-size: 14px; 
  margin-top: 8px; 
  text-align: center; 
  line-height: 1.6;
  font-weight: 400;
}
h2 {
  color: #2c3e50;
  font-size: 24px;
  margin-bottom: 22px;
  letter-spacing: 0.5px;
  font-weight: 700;
  line-height: 1.3;
}
h3 {
  color: #34495e;
  font-size: 20px;
  margin-bottom: 16px;
  letter-spacing: 0.3px;
  font-weight: 600;
  line-height: 1.4;
}
p, span, div {
  color: #2c3e50;
  line-height: 1.6;
}
.annotate-box h2 {
  color: #1677ff;
  font-size: 22px;
  text-align: center;
  margin-bottom: 24px;
  font-weight: 600;
}

input[type="password"], input[type="text"] {
  margin-bottom: 16px;
}
/* 额外的字体美化 */
.dataset-card h2, .login-card h2 {
  color: #2c3e50;
  font-size: 24px;
  margin-bottom: 24px;
  letter-spacing: 0.5px;
  font-weight: 700;
  text-align: center;
}
.selector-header h2 {
  color: #2c3e50;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 0.3px;
}
/* 图片选择器中的文字 */
.dataset-card div[style*="fontSize:18"] {
  font-size: 19px !important;
  color: #34495e !important;
  font-weight: 600 !important;
  line-height: 1.5 !important;
}
.dataset-card div[style*="fontSize:14"] {
  font-size: 15px !important;
  color: #7f8c8d !important;
  font-weight: 500 !important;
  line-height: 1.6 !important;
}
/* 用户名加粗显示 */
.top-bar b {
  color: #1677ff;
  font-weight: 700;
}
/* 角色显示 */
.top-bar span {
  font-weight: 500;
  color: #34495e;
}
/* 图片选择器样式 */
.image-selector-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid #e6e6e6;
  transition: all 0.2s ease;
}
.image-selector-item:hover {
  border-color: #1677ff;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.1);
}
.image-selector-thumb {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  margin-right: 16px;
  object-fit: cover;
}
.image-selector-id {
  font-weight: 700;
  margin-bottom: 6px;
  font-size: 16px;
  color: #2c3e50;
  letter-spacing: 0.3px;
}
.image-selector-status {
  font-size: 15px;
}
.status-annotated {
  color: #059669;
  font-weight: 600;
}
.status-pending {
  color: #f59e0b;
  font-weight: 600;
}
.loading-text {
  text-align: center;
  padding: 20px;
  font-size: 16px;
  color: #6b7280;
  font-weight: 500;
}
.empty-state {
  text-align: center;
  padding: 40px 20px;
}
.empty-title {
  font-size: 19px;
  color: #9ca3af;
  margin-bottom: 16px;
  font-weight: 600;
}
.empty-subtitle {
  font-size: 15px;
  color: #6b7280;
  font-weight: 500;
  line-height: 1.6;
}

/* 数据集管理器样式 */
.admin-controls {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: rgba(116, 185, 255, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(116, 185, 255, 0.2);
}

.admin-btn {
  background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(116, 185, 255, 0.3);
}

.admin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(116, 185, 255, 0.4);
}

.admin-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.form-container {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e8ed;
}

.form-row {
  margin-bottom: 16px;
}

.form-row label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #2c3e50;
}

.input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

.input:focus {
  outline: none;
  border-color: #74b9ff;
  box-shadow: 0 0 0 3px rgba(116, 185, 255, 0.1);
}

.select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

.select:focus {
  outline: none;
  border-color: #74b9ff;
  box-shadow: 0 0 0 3px rgba(116, 185, 255, 0.1);
}

.label-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e1e8ed;
}

.label-section h3 {
  margin-bottom: 8px;
  color: #2c3e50;
}

.hint-text {
  font-size: 13px;
  color: #74798c;
  margin-bottom: 16px;
  line-height: 1.5;
}

.label-input-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  align-items: center;
}

.label-name-input {
  flex: 1;
}

.btn-icon {
  background: #e74c3c;
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  transition: all 0.3s ease;
}

.btn-icon:hover {
  background: #c0392b;
  transform: scale(1.1);
}

/* 添加边框卡片效果 */
.btn-text {
  background: white;
  border: 2px solid transparent;
  color: #666;
  cursor: pointer;
  font-weight: 600;
  font-size: 11px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: fit-content;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  position: relative;
  overflow: hidden;
}

.btn-text:hover {
  color: #0984e3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.btn-text::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  transition: left 0.5s;
}

.btn-text:hover::before {
  left: 100%;
}


.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e1e8ed;
}

.cancel-btn {
  background: #bdc3c7;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background: #95a5a6;
}

.file-input {
  width: 100%;
  padding: 12px;
  border: 2px dashed #74b9ff;
  border-radius: 8px;
  background: rgba(116, 185, 255, 0.05);
  cursor: pointer;
  transition: all 0.3s ease;
}

.file-input:hover {
  background: rgba(116, 185, 255, 0.1);
  border-color: #0984e3;
}

.file-preview {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
  border: 1px solid #e1e8ed;
}

.file-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
}

.file-list li {
  padding: 4px 0;
  font-size: 13px;
  color: #74798c;
}

.progress-bar-container {
  position: relative;
  width: 100%;
  height: 8px;
  background: #e1e8ed;
  border-radius: 4px;
  margin-top: 16px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #74b9ff 0%, #0984e3 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: -24px;
  right: 0;
  font-size: 12px;
  font-weight: 600;
  color: #74b9ff;
}

.datasets-list {
  margin-top: 32px;
}

.datasets-list h3 {
  margin-bottom: 16px;
  color: #2c3e50;
}

.loading-text {
  text-align: center;
  padding: 24px;
  color: #74798c;
  font-style: italic;
}

.dataset-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e1e8ed;
}

.dataset-table-header {
  display: grid;
  grid-template-columns: 60px 1fr 100px 300px;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 1px solid #e1e8ed;
  justify-content: flex-start;
}
  
.dataset-table-row {
  display: grid;
  grid-template-columns: 60px 1fr 100px 300px;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #f1f3f4;
  transition: background-color 0.3s ease;
}

.dataset-table-row:hover {
  background: #f8fafc;
}

.dataset-table-row:last-child {
  border-bottom: none;
}

.col-id {
  font-weight: 600;
  color: #74b9ff;
}

.col-name {
  font-weight: 500;
}

.col-count {
  text-align: center;
  color: #74798c;
}

.col-actions {
  text-align: center;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 150px;
}

.delete-btn {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  color: #c62828;
}

.delete-btn:hover {
  color: #c0392b;
  background: linear-gradient(135deg, #ffcdd2 0%, #ef9a9a 100%);
}

.manage-btn {
  color: #1677ff;
  margin-right: 8px;
  font-size: 13px;
  font-weight: 600;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
}

.manage-btn:hover {
  color: #0d4f8c;
  background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
}

.fix-btn {
  color: #10b981;
  margin-right: 8px;
  font-size: 13px;
  font-weight: 600;
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
}

.fix-btn:hover {
  color: #059669;
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
}

.back-btn {
  background: #74798c;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: #5a6c7d;
}

@media (max-width: 900px) {
  .main-bg { max-width: 98vw; padding: 18px 2vw; }
  .top-bar { flex-direction: column; gap: 10px; align-items: flex-start; }
  .login-card { padding: 28px 8vw 18px 8vw; }
  .logo-container { position: relative; right: auto; top: auto; transform: none; margin: 10px 0; }
  .selector-header { flex-direction: column; gap: 12px; align-items: stretch; }
  .selector-header h2 { margin-bottom: 0; text-align: center; }
  .progress-section { flex-direction: column; align-items: center; padding: 16px; }
  .progress-visual { justify-content: center; flex-direction: column; gap: 16px; }
  .progress-stats { gap: 12px; }
  .stat-number { font-size: 20px; }
  .control-buttons { flex-wrap: wrap; }
}

/* 用户管理相关样式 */
.config-info {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.info-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 12px;
}

.info-content p {
  margin: 8px 0;
  font-size: 14px;
  color: #495057;
}

.info-content code {
  background: #f1f3f4;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
}

.instructions {
  margin: 12px 0;
}

.instructions ol {
  margin: 8px 0 0 20px;
  padding: 0;
}

.instructions li {
  margin: 4px 0;
  font-size: 14px;
  color: #495057;
}

.stats {
  display: flex;
  gap: 20px;
  margin-top: 12px;
  font-size: 14px;
  color: #6c757d;
}

.users-list h4 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 18px;
}

.user-table {
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.user-table-header {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #e1e5e9;
  padding: 12px 16px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

.user-table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f3f4;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

.user-table-row:hover {
  background: #f8f9fa;
}

.user-table-row:last-child {
  border-bottom: none;
}

.col-username {
  font-weight: 500;
  color: #2c3e50;
}

.col-role {
  display: flex;
  align-items: center;
}

.role-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
}

.role-admin {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  color: #c62828;
}

.role-doctor {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  color: #1565c0;
}

.role-student {
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  color: #2e7d32;
}

.col-description {
  color: #6c757d;
  font-size: 13px;
}
`;
document.head.appendChild(style);


