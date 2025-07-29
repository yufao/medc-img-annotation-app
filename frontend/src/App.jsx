import React, { useState, useEffect } from 'react';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export default function App() {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState('');
  const [dataset, setDataset] = useState(null);
  const [selectMode, setSelectMode] = useState(false);
  const [selectedImageId, setSelectedImageId] = useState(null);

  if (!user) return <div className="login-bg"><Login onLogin={(u, r) => handleLogin(u, r)} /></div>;
  if (!dataset) return <div className="select-bg"><DatasetSelect user={user} onSelect={setDataset} /></div>;
  if (selectMode) return <div className="select-bg"><ImageSelector user={user} dataset={dataset} role={role} onSelect={handleImageSelect} /></div>;

  return (
    <div className="main-bg">
      <div className="top-bar">
        <span>用户: <b>{user}</b> ({role})</span>
        <button className="btn logout" onClick={handleLogout}>退出</button>
      </div>
      <Annotate 
        user={user} 
        dataset={dataset} 
        role={role}
        onDone={handleAnnotationDone} 
        imageIdInit={selectedImageId} 
      />
      <div className="export-bar">
        <Export />
        <button className="btn" onClick={() => setSelectMode(true)}>选择图片/修改标注</button>
      </div>
    </div>
  );

  function handleLogin(username, role) {
    setUser(username);
    setRole(role);
  }

  function handleLogout() {
    setUser(null);
    setDataset(null);
  }

  function handleImageSelect(id) {
    setSelectedImageId(id);
    setSelectMode(false);
  }

  function handleAnnotationDone() {
    setDataset(null);
    setSelectedImageId(null);
  }
}

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');

  const handleLogin = async () => {
    try {
      const res = await api.post('/login', { username, password });
      onLogin(username, res.data.role);
    } catch (error) {
      setMsg('登录失败');
    }
  };

  return (
    <div className="login-card">
      <h2>用户登录</h2>
      <div className="form-row">
        <input className="input" placeholder="用户名" value={username} onChange={e=>setUsername(e.target.value)} />
      </div>
      <div className="form-row">
        <input className="input" type="password" placeholder="密码" value={password} onChange={e=>setPassword(e.target.value)} />
      </div>
      <button className="btn login-btn" onClick={handleLogin} style={{width:'100%',margin:'18px 0 8px 0'}}>
        登录
      </button>
      <div className="login-msg">{msg}</div>
      <div className="login-tip">测试账号：admin/admin123、doctor/doctor123、student/student123</div>
    </div>
  );
}

function DatasetSelect({ user, onSelect }) {
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

function Annotate({ user, dataset, role, onDone, imageIdInit }) {
  const [img, setImg] = useState(null);
  const [labels, setLabels] = useState([]);
  const [label, setLabel] = useState('');
  const [remark, setRemark] = useState('');
  const [imageId, setImageId] = useState(imageIdInit);

  useEffect(() => {
    if (dataset) {
      api.get('/labels', { params: { dataset_id: dataset.id } }).then(r => setLabels(r.data));
    }
  }, [dataset]);

  useEffect(() => {
    if (dataset && user) {
      fetchImage(imageId || null);
    }
  }, [dataset, user, imageId]);

  const fetchImage = async (id) => {
    try {
      if (id) {
        // 获取指定图片及其标注信息
        const { data } = await api.post('/images_with_annotations', {
          dataset_id: dataset.id,
          expert_id: user,
          image_id: id
        });
        if (data.length > 0) {
          const found = data[0];
          setImg(found);
          setLabel(found.annotation?.label || '');
          setRemark(found.annotation?.tip || '');
          return;
        }
      }
      // 获取下一个待标注图片（根据当前用户角色）
      const { data } = await api.post('/next_image', {
        expert_id: user,
        dataset_id: dataset.id,
        role: role // 添加角色信息，确保不同角色的进度独立
      });
      if (data.image_id) {
        setImg({ image_id: data.image_id, filename: data.filename });
        setLabel('');
        setRemark('');
        setImageId(data.image_id);
      } else {
        setImg(null);
      }
    } catch (error) {
      console.error("获取图片失败:", error);
      setImg(null);
    }
  };

  const handleSubmit = async () => { // 定义 handleSubmit 函数
    try {
      await api.post('/annotate', {
        expert_id: user,
        dataset_id: dataset.id,
        image_id: img.image_id,
        label,
        tip: remark
      });
      setLabel('');
      setRemark('');
      fetchImage();
    } catch (error) {
      console.error("提交标注失败:", error);
    }
  };

  const handlePrev = async () => { // 定义 handlePrev 函数
    try {
      const { data } = await api.post('/prev_image', {
        dataset_id: dataset.id,
        image_id: img.image_id
      });
      if (data.image_id) fetchImage(data.image_id);
    } catch (error) {
      console.error("获取上一张图片失败:", error);
    }
  };

  if (!img) return <div className="done-box">标注完成！<button className="btn" onClick={onDone}>返回</button></div>;

  return (
    <div className="annotate-box">
      <h2>标注图片: </h2>
      {img && (
        <div style={{ textAlign: 'center', marginBottom: '20px 0' }}>
          <img src={`/static/img/${img.filename}`} alt={img.filename} style={{ maxWidth: '90%', maxHeight: '400px', borderRadius: '18px', boxShadow: '0 2px 16px rgba(0,0,0,0.1)' }} />
          <div className="img-name">{img.filename}</div>
        </div>
      )}
      <div className="form-row label-row">
        <label>标签：</label>
        <div className="label-btn-group">
          {labels.map(l => (
            <button
              key={l.label_id}
              type="button"
              className={"label-btn" + (label === l.label_id ? " selected" : "")}
              onClick={() => setLabel(l.label_id)}
            >{l.name}</button>
          ))}
        </div>
      </div>
      <div className="form-row">
        <label>备注：</label>
        <input className="input" value={remark} onChange={e => setRemark(e.target.value)} placeholder="可选" />
      </div>
      <button className="btn" onClick={handleSubmit} disabled={!label}>提交并下一张</button>
      <button className="btn" onClick={handlePrev} style={{ marginLeft: 12 }}>上一张</button>
    </div>
  );
}

function ImageSelector({ user, dataset, role, onSelect, pageSize = 20 }) {
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
      <h2>选择图片进行标注/修改</h2>
      <div style={{maxHeight:500,overflowY:'auto'}}>
        {images.map(img=>(
          <div key={img.image_id} style={{display:'flex',alignItems:'center',marginBottom:12,padding:12,borderRadius:8,border:'1px solid #e6e6e6'}}>
            <img src={`/static/img/${img.filename}`} alt={img.filename} style={{width:60,height:60,borderRadius:8,marginRight:16}} />
            <div style={{flex:1}}>
              <div style={{fontWeight:'bold',marginBottom:4}}>{img.filename}</div>
              <div style={{fontSize:14,color:'#666'}}>
                {img.annotation ? (
                  <span style={{color:'#52c41a'}}>
                    ✓ 已标注: {img.annotation.label_name || img.annotation.label}
                    {img.annotation.tip && ` (${img.annotation.tip})`}
                  </span>
                ) : (
                  <span style={{color:'#fa8c16'}}>○ 未标注</span>
                )}
              </div>
            </div>
            <button className="btn" onClick={()=>onSelect(img.image_id)}>
              {img.annotation ? '修改标注' : '开始标注'}
            </button>
          </div>
        ))}
        {loading && <div style={{textAlign:'center',padding:16}}>加载中...</div>}
        {!loading && images.length === 0 && (
          <div style={{textAlign:'center',padding:32}}>
            <div style={{fontSize:18,color:'#999',marginBottom:16}}>暂无图片数据</div>
            <div style={{fontSize:14,color:'#666'}}>请检查数据集是否包含图片，或联系管理员</div>
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

function Export() {
  const handleExport = () => {
    window.open('/api/export', '_blank');
  };
  return <button className='btn' onClick={handleExport}>导出Excel</button>;
}

const style = document.createElement('style');
style.innerHTML = `
body {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
  font-family: 'Inter', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
  letter-spacing: 0.02em;
}
.main-bg {
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
  font-size: 18px;
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
  color: #444;
  font-weight: 600;
  letter-spacing: 1px;
  font-size: 17px;
  margin-top: 8px;
}
.select, .input {
  flex: 1;
  padding: 13px 16px;
  border: 1.5px solid #bfc7d1;
  border-radius: 8px;
  font-size: 17px;
  outline: none;
  transition: border 0.2s, box-shadow 0.2s;
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
  background: linear-gradient(90deg, #e0e7ff 0%, #8ec5fc 100%);
  color: #1677ff;
  border: none;
  border-radius: 18px;
  padding: 12px 32px;
  font-size: 17px;
  margin: 4px 0;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px #8ec5fc33;
  transition: background 0.2s, color 0.2s, box-shadow 0.2s, transform 0.1s;
}
.label-btn.selected, .label-btn:hover {
  background: linear-gradient(90deg, #4f8cff 0%, #1677ff 100%);
  color: #fff;
  box-shadow: 0 4px 16px #1677ff33;
  transform: scale(1.06);
}
.img-name {
  color: #1677ff;
  font-weight: bold;
  font-size: 22px;
}
.done-box {
  text-align: center;
  margin: 100px 0;
  font-size: 22px;
  color: #1677ff;
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
.login-msg { color: #f5222d; min-height: 24px; font-size: 15px; }
.login-tip { color: #888; font-size: 13px; margin-top: 8px; text-align: center; }
h2 {
  color: #222;
  font-size: 26px;
  margin-bottom: 22px;
  letter-spacing: 1px;
  font-weight: 700;
}

input[type="password"], input[type="text"] {
  margin-bottom: 16px;
}
@media (max-width: 900px) {
  .main-bg { max-width: 98vw; padding: 18px 2vw; }
  .top-bar { flex-direction: column; gap: 10px; align-items: flex-start; }
  .login-card { padding: 28px 8vw 18px 8vw; }
}
`;
document.head.appendChild(style);


