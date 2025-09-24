import React from 'react';

export default function ProgressPanel({ annotated, total }) {
  const remaining = Math.max(0, total - annotated);
  const percent = total > 0 ? Math.round((annotated / total) * 100) : 0;
  return (
    <div className="progress-panel">
      <div className="progress-row">
        <div className="metric"><span className="value">{annotated}</span><span className="label">已标注</span></div>
        <div className="metric"><span className="value">{remaining}</span><span className="label">剩余</span></div>
        <div className="metric"><span className="value">{total}</span><span className="label">总计</span></div>
        <div className="metric"><span className="value">{percent}%</span><span className="label">进度</span></div>
      </div>
      <div className="progress-bar">
        <div className="progress-bar-inner" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
