import React, { useEffect, useState } from 'react';
import api from '../../api/client';

function UserManager({ role }) {
  const [users, setUsers] = useState([]);
  const [configInfo, setConfigInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchUsers(); fetchConfigInfo(); }, []);
  const fetchUsers = async () => { try { const r = await api.get(`/admin/users?role=${role}`); setUsers(r.data || []); } catch { setUsers([]); } };
  const fetchConfigInfo = async () => { try { const r = await api.get(`/admin/users/config?role=${role}`); setConfigInfo(r.data); } catch {} finally { setLoading(false); } };
  if (loading) return <div className="form-container"><h3>用户管理</h3><div className="loading-text">加载用户信息...</div></div>;
  return (
    <div className="form-container"><h3>用户管理</h3>
      {configInfo && <div className="config-info"><div className="info-title">📝 用户管理说明</div><div className="info-content"><p><strong>管理方式：</strong>{configInfo.message}</p><p><strong>配置文件：</strong><code>{configInfo.config_file}</code></p><div className="instructions"><strong>操作步骤：</strong><ol>{configInfo.instructions.map((i,idx)=><li key={idx}>{i}</li>)}</ol></div><div className="stats"><span>当前用户数量: <strong>{configInfo.current_users_count}</strong></span><span>角色映射: {Object.entries(configInfo.roles_mapping).map(([r,id])=>`${r}(${id})`).join(', ')}</span></div></div></div>}
      <div className="users-list"><h4>当前系统用户</h4>{users.length===0? <div className="empty-state"><div className="empty-title">无法获取用户信息</div><div className="empty-subtitle">请检查权限或联系系统管理员</div></div> : <div className="user-table"><div className="user-table-header"><div className="col-username">用户名</div><div className="col-role">角色</div><div className="col-description">描述</div></div>{users.map((u,i)=>(<div key={i} className="user-table-row"><div className="col-username">{u.username}</div><div className="col-role"><span className={`role-badge role-${u.role}`}>{u.role==='admin'?'管理员':u.role==='doctor'?'医生':'学生'}</span></div><div className="col-description">{u.description}</div></div>))}</div>}</div>
    </div>
  );
}

export default function DatasetManager({ user, role, onBack }) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [showLabelManager, setShowLabelManager] = useState(false);
  const [showUserManager, setShowUserManager] = useState(false);
  const [editingDatasetId, setEditingDatasetId] = useState(null);
  const [datasetLabels, setDatasetLabels] = useState([]);
  const [newDatasetName, setNewDatasetName] = useState('');
  const [newDatasetDesc, setNewDatasetDesc] = useState('');
  const [labelInputs, setLabelInputs] = useState([{ name: '', category: '病理学' }]);
  const [multiSelect, setMultiSelect] = useState(false);
  const [files, setFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => { fetchDatasets(); }, []);
  const fetchDatasets = async () => { setLoading(true); try { const r = await api.get('/datasets'); setDatasets(r.data || []); } catch { } finally { setLoading(false); } };
  const fetchDatasetLabels = async (datasetId) => { try { const r = await api.get(`/admin/datasets/${datasetId}/labels?role=${role}`); const labels = r.data.map(l => ({ name: l.label_name, category: l.category || '病理学' })); setDatasetLabels(labels.length?labels:[{ name:'', category:'病理学'}]); } catch { setDatasetLabels([{ name:'', category:'病理学'}]); } };
  const handleCreateDataset = async () => { if (!newDatasetName.trim()) { alert('请输入数据集名称'); return; } try { const res = await api.post('/admin/datasets', { name: newDatasetName, description: newDatasetDesc, multi_select: multiSelect, role }); if (res.data.msg==='success') { const validLabels = labelInputs.filter(l=>l.name.trim()!==''); if (validLabels.length) await api.post(`/admin/datasets/${res.data.dataset_id}/labels`, { labels: validLabels, role }); alert('数据集创建成功!'); setNewDatasetName(''); setNewDatasetDesc(''); setLabelInputs([{ name:'', category:'病理学'}]); setMultiSelect(false); setShowCreateForm(false); fetchDatasets(); } } catch (e) { alert(`创建失败: ${e.response?.data?.error||e.message}`); } };
  const handleDeleteDataset = async (datasetId) => { if (!window.confirm('确认删除此数据集? 此操作不可恢复!')) return; try { const res = await api.delete(`/admin/datasets/${datasetId}?role=${role}`); if (res.data.msg==='success') { alert('数据集删除成功!'); fetchDatasets(); } } catch (e) { alert(`删除失败: ${e.response?.data?.error||e.message}`); } };
  const handleFileChange = e => setFiles(Array.from(e.target.files));
  const handleUpload = async () => { if (!selectedDataset) { alert('请先选择数据集'); return; } if (!files.length) { alert('请选择至少一张图片'); return; } const formData = new FormData(); formData.append('role', role); files.forEach(f=>formData.append('images', f)); try { const res = await api.post(`/admin/datasets/${selectedDataset.id}/images`, formData, { headers:{'Content-Type':'multipart/form-data'}, onUploadProgress: p => setUploadProgress(Math.round((p.loaded*100)/p.total)) }); if (res.data.msg==='success') { alert(`上传成功! 成功上传 ${res.data.uploaded} 张图片, 失败 ${res.data.failed} 张`); setFiles([]); setUploadProgress(0); setShowUploadForm(false); fetchDatasets(); } } catch (e) { alert(`上传失败: ${e.response?.data?.error||e.message}`); } };
  const addLabelInput = () => setLabelInputs([...labelInputs, { name:'', category:'病理学'}]);
  const updateLabelInput = (i, field, value) => { const updated=[...labelInputs]; updated[i][field]=value; setLabelInputs(updated); };
  const removeLabelInput = (i) => { const updated=[...labelInputs]; updated.splice(i,1); setLabelInputs(updated); };

  return (
    <div className="dataset-card" style={{maxWidth:800}}>
      <div className="selector-header"><h2>数据集管理面板</h2><button className="btn back-btn" onClick={onBack}>返回</button></div>
      <div className="admin-controls">
        <button className="btn admin-btn" onClick={() => { setShowCreateForm(true); setShowUploadForm(false); setShowUserManager(false); }}>创建新数据集</button>
        <button className="btn admin-btn" onClick={() => { setShowUploadForm(true); setShowCreateForm(false); setShowUserManager(false); }} disabled={!datasets.length}>上传图片</button>
        <button className="btn admin-btn" onClick={() => { setShowUserManager(true); setShowCreateForm(false); setShowUploadForm(false); }}>用户管理</button>
      </div>
      {showCreateForm && (
        <div className="form-container">
          <h3>创建新数据集</h3>
          <div className="form-row"><label>数据集名称:</label><input className="input" value={newDatasetName} onChange={e=>setNewDatasetName(e.target.value)} placeholder="例如: 肺炎CT图像集" /></div>
          <div className="form-row"><label>数据集描述:</label><textarea className="input" value={newDatasetDesc} onChange={e=>setNewDatasetDesc(e.target.value)} placeholder="描述该数据集的用途和内容" style={{minHeight:80}} /></div>
          <div className="form-row"><label>多标签模式:</label><input type="checkbox" checked={multiSelect} onChange={e=>setMultiSelect(e.target.checked)} /> <span className="hint-text">允许单张图片选择多个标签（ORD5K/NIH 等多病症场景）</span></div>
            <div className="label-section"><h3>标签配置</h3><p className="hint-text">添加该数据集的标签选项，标注时将使用这些标签</p>{labelInputs.map((l,i)=>(<div key={i} className="label-input-row"><input className="input label-name-input" value={l.name} onChange={e=>updateLabelInput(i,'name',e.target.value)} placeholder="标签名称" /><select className="select" value={l.category} onChange={e=>updateLabelInput(i,'category',e.target.value)}><option value="病理学">病理学</option><option value="解剖学">解剖学</option><option value="影像学">影像学</option></select><button className="btn-icon remove-btn" onClick={()=>removeLabelInput(i)} title="移除此标签">×</button></div>))}<button className="btn-text" onClick={addLabelInput}>+ 添加标签</button></div>
          <div className="form-actions"><button className="btn cancel-btn" onClick={()=>setShowCreateForm(false)}>取消</button><button className="btn" onClick={handleCreateDataset}>创建数据集</button></div>
        </div>
      )}
      {showUploadForm && (
        <div className="form-container">
          <h3>上传图片</h3>
          <div className="form-row"><label>选择数据集:</label><select className="select" value={selectedDataset?selectedDataset.id:''} onChange={e=>{ const id=parseInt(e.target.value); const ds=datasets.find(d=>d.id===id); setSelectedDataset(ds); }}><option value="">-- 选择数据集 --</option>{datasets.map(ds=><option key={ds.id} value={ds.id}>{ds.name}</option>)}</select></div>
          <div className="form-row"><label>选择图片:</label><input type="file" multiple accept="image/*" onChange={handleFileChange} className="file-input" /><p className="hint-text">支持jpg, png, jpeg等图片格式，可多选</p></div>
          {files.length>0 && (<div className="file-preview"><p>已选择 {files.length} 个文件</p><ul className="file-list">{files.slice(0,5).map((f,i)=><li key={i}>{f.name} ({(f.size/1024).toFixed(1)} KB)</li>)}{files.length>5 && <li>...等 {files.length-5} 个文件</li>}</ul></div>)}
          {uploadProgress>0 && (<div className="progress-bar-container"><div className="progress-bar" style={{width:`${uploadProgress}%`}} /><span className="progress-text">{uploadProgress}%</span></div>)}
          <div className="form-actions"><button className="btn cancel-btn" onClick={()=>setShowUploadForm(false)}>取消</button><button className="btn" onClick={handleUpload} disabled={!selectedDataset || !files.length}>上传图片</button></div>
        </div>
      )}
      {showLabelManager && (
        <div className="form-container"><h3>管理数据集 #{editingDatasetId} 标签</h3><div className="label-section">{datasetLabels.map((l,i)=>(<div key={i} className="label-input-row"><input className="input label-name-input" value={l.name} onChange={e=>{ const updated=[...datasetLabels]; updated[i].name=e.target.value; setDatasetLabels(updated); }} placeholder="标签名称" /><select className="select" value={l.category} onChange={e=>{ const updated=[...datasetLabels]; updated[i].category=e.target.value; setDatasetLabels(updated); }}><option value="病理学">病理学</option><option value="解剖学">解剖学</option><option value="影像学">影像学</option></select><button className="btn-icon remove-btn" onClick={()=>{ const updated=[...datasetLabels]; updated.splice(i,1); setDatasetLabels(updated); }} title="移除此标签">×</button></div>))}<button className="btn-text" onClick={()=>setDatasetLabels([...datasetLabels,{ name:'', category:'病理学'}])}>+ 添加标签</button></div><div className="form-actions"><button className="btn cancel-btn" onClick={()=>setShowLabelManager(false)}>取消</button><button className="btn" onClick={async()=>{ try { const valid = datasetLabels.filter(l=>l.name.trim()!==''); const r = await api.put(`/admin/datasets/${editingDatasetId}/labels`, { labels: valid, role }); if (r.data.msg==='success') { alert('标签更新成功!'); setShowLabelManager(false); } } catch (e) { alert(`更新失败: ${e.response?.data?.error||e.message}`); } }}>保存标签</button></div></div>
      )}
      {showUserManager && <UserManager role={role} />}
      <div className="datasets-list"><h3>现有数据集</h3>{loading ? <div className="loading-text">加载数据集...</div> : datasets.length===0 ? (<div className="empty-state"><div className="empty-title">暂无数据集</div><div className="empty-subtitle">点击"创建新数据集"按钮创建您的第一个数据集</div></div>) : (<div className="dataset-table"><div className="dataset-table-header"><div className="col-id">ID</div><div className="col-name">名称</div><div className="col-count">图片数量</div><div className="col-count">多标签</div><div className="col-actions">操作</div></div>{datasets.map(ds => (<div key={ds.id} className="dataset-table-row"><div className="col-id">{ds.id}</div><div className="col-name">{ds.name}</div><div className="col-count">{ds.image_count || 0}</div><div className="col-count">{ds.multi_select ? '是' : '否'}</div><div className="col-actions"><button className="btn-text manage-btn" onClick={()=>{ setEditingDatasetId(ds.id); fetchDatasetLabels(ds.id); setShowLabelManager(true); }}>管理标签</button><button className="btn-text fix-btn" onClick={async()=>{ try { const r = await api.post(`/admin/datasets/${ds.id}/recount`, { role }); if (r.data.msg==='success') { alert(`图片数量已更新为: ${r.data.image_count}`); fetchDatasets(); } } catch (e) { alert(`修正失败: ${e.response?.data?.error||e.message}`); } }}>修正统计</button><button className="btn-text danger-btn" onClick={async()=>{ if(!window.confirm('确认清空该数据集的所有标注记录？此操作不可恢复。')) return; try { const r = await api.delete(`/admin/datasets/${ds.id}/annotations?role=${role}`); if(r.data.msg==='success'){ alert('标注已清空'); } } catch(e){ alert(`清空失败: ${e.response?.data?.error||e.message}`); } }}>清空标注</button><button className="btn-text delete-btn" onClick={()=>handleDeleteDataset(ds.id)}>删除</button></div></div>))}</div>)}
      </div>
    </div>
  );
}
