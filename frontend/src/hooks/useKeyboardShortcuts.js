import { useEffect } from 'react';

// 支持：ArrowLeft/ArrowRight 切换上一张/提交下一张；数字键 1-9 选标签
export function useKeyboardShortcuts({ onPrev, onSubmit, onSelectLabel, enabled = true }) {
  useEffect(() => {
    if (!enabled) return;
    const handler = (e) => {
      if (['INPUT','TEXTAREA'].includes(e.target.tagName)) return; // 避免输入框干扰
      if (e.key === 'ArrowLeft') { e.preventDefault(); onPrev && onPrev(); }
      if (e.key === 'ArrowRight') { e.preventDefault(); onSubmit && onSubmit(); }
      if (/^[1-9]$/.test(e.key)) { onSelectLabel && onSelectLabel(Number(e.key)); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onPrev, onSubmit, onSelectLabel, enabled]);
}

export default useKeyboardShortcuts;
