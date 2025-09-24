import React, { useState } from 'react';
import api from '../api/client';

export default function Login({ onLogin }) {
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
      <div className="login-tip">请使用系统分配的账号登录</div>
    </div>
  );
}
