import React, { useState } from 'react';

export default function ExportButton({ dataset, user }) {
  const [exporting, setExporting] = useState(false);
  const handleExport = () => {
    setExporting(true);
    let exportUrl = '/api/export';
    const params = [];
    if (dataset?.id) params.push(`dataset_id=${dataset.id}`);
    if (user) params.push(`expert_id=${user}`);
    if (params.length) exportUrl += '?' + params.join('&');
    window.open(exportUrl, '_blank');
    setTimeout(() => setExporting(false), 2000);
  };
  return (
    <button className={`btn ${exporting ? 'exporting' : ''}`} onClick={handleExport} disabled={exporting}>
      {exporting ? '导出中...' : '导出Excel'}
    </button>
  );
}
