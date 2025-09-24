import React, { useEffect, useState } from 'react';
import api from '../api/client';

export default function DatasetSelect({ user, role, onSelect, onAdmin }) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDatasets = async () => {
      setLoading(true);
      try {
        const response = await api.get('/datasets', { params: { user_id: user } });
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
          <button className="btn admin-btn" onClick={onAdmin}>管理数据集</button>
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
              key={ds.id || ds.name || index}
              className="dataset-btn"
              onClick={() => onSelect(ds)}
            >{ds.name}</button>
          ))}
        </div>
      )}
    </div>
  );
}
