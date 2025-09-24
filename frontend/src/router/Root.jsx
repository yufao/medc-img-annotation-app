import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Login from '../components/Login';
import DatasetSelect from '../components/DatasetSelect';
import DatasetManager from '../components/admin/DatasetManager';
import ImageSelector from '../components/annotation/ImageSelector';
import Annotate from '../components/annotation/Annotate';
import ExportButton from '../components/annotation/ExportButton';
import useAppStore from '../store/useAppStore';
import '../styles/app.css';
import '../styles/annotation.css';
import '../styles/admin.css';
import '../styles/auth.css';

function RequireAuth({ children }) {
  const user = useAppStore(s => s.user);
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function LayoutAnnotate() {
  const { user, role, dataset, setDataset } = useAppStore(s => ({
    user: s.user, role: s.role, dataset: s.dataset, setDataset: s.setDataset
  }));
  const navigate = useNavigate();
  if (!dataset) return <Navigate to="/datasets" replace />;
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
          <button className="btn logout" onClick={() => { setDataset(null); navigate('/datasets'); }}>返回</button>
        </div>
        <Annotate user={user} dataset={dataset} role={role} onDone={() => { setDataset(null); navigate('/datasets'); }} />
        <div className="export-bar">
          <ExportButton dataset={dataset} user={user} role={role} />
          <button className="btn" onClick={() => navigate('/images')}>选择图片/修改标注</button>
        </div>
      </div>
    </div>
  );
}

function ImagesPage() {
  const { dataset, user, role } = useAppStore(s => ({ dataset: s.dataset, user: s.user, role: s.role }));
  const navigate = useNavigate();
  if (!dataset) return <Navigate to="/datasets" replace />;
  return (
    <div className="select-bg">
      <ImageSelector user={user} dataset={dataset} role={role} onSelect={() => navigate('/annotate')} onBack={() => navigate('/annotate')} />
    </div>
  );
}

function DatasetsPage() {
  const { role } = useAppStore();
  const setDataset = useAppStore(s => s.setDataset);
  const navigate = useNavigate();
  return (
    <div className="select-bg">
      <DatasetSelect onSelect={(ds) => { setDataset(ds); navigate('/annotate'); }} role={role} onAdmin={() => role === 'admin' && navigate('/admin/datasets')} />
    </div>
  );
}

function AdminDatasetsPage() {
  const { user, role } = useAppStore();
  const navigate = useNavigate();
  return (
    <div className="select-bg"><DatasetManager user={user} role={role} onBack={() => navigate('/datasets')} /></div>
  );
}

function LoginPage() {
  const setUser = useAppStore(s => s.setUser);
  const navigate = useNavigate();
  return (
    <div className="login-bg"><Login onLogin={(u, r) => { setUser(u, r); navigate('/datasets'); }} /></div>
  );
}

export default function Root() {
  // 可加首次初始化副作用（例如读取本地缓存）
  useEffect(() => {
    // 占位：未来从 localStorage 恢复 session
  }, []);
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/datasets" element={<RequireAuth><DatasetsPage /></RequireAuth>} />
        <Route path="/annotate" element={<RequireAuth><LayoutAnnotate /></RequireAuth>} />
        <Route path="/images" element={<RequireAuth><ImagesPage /></RequireAuth>} />
        <Route path="/admin/datasets" element={<RequireAuth><AdminDatasetsPage /></RequireAuth>} />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
