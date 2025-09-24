"""Dataset service layer (Phase 2 -> Phase 3) consolidating dataset-related operations.

Now delegates raw persistence to repository & adds lightweight in-memory cache for statistics.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from app.core.db import get_db, USE_DATABASE
from app.repositories import dataset_repository
from db_utils import get_next_sequence_value  # type: ignore  # retained for backward compat (create may still use if repo evolves)

class DatasetService:
    def __init__(self):
        self.db = None  # lazy acquire

    def ensure_db(self):
        # 允许在运行时重新获取（启动早期顺序导致的 None 问题）
        if self.db is None or not USE_DATABASE:
            self.db = get_db()
        if not USE_DATABASE or self.db is None:
            raise RuntimeError("数据库连接不可用")

    # --- Caches ---
    _stats_cache: Dict[Tuple[int, Optional[str]], Dict[str, Any]] = {}
    _stats_cache_expiry: Dict[Tuple[int, Optional[str]], datetime] = {}
    _STATS_TTL = timedelta(seconds=15)

    def _cache_get_stats(self, dataset_id: int, expert_id: Optional[str]):
        key = (dataset_id, expert_id)
        exp = self._stats_cache_expiry.get(key)
        if exp and exp > datetime.now():
            return self._stats_cache.get(key)
        self._stats_cache.pop(key, None)
        self._stats_cache_expiry.pop(key, None)
        return None

    def _cache_set_stats(self, dataset_id: int, expert_id: Optional[str], value: Dict[str, Any]):
        key = (dataset_id, expert_id)
        self._stats_cache[key] = value
        self._stats_cache_expiry[key] = datetime.now() + self._STATS_TTL

    def invalidate_stats(self, dataset_id: int, expert_id: Optional[str] = None):
        keys = [k for k in list(self._stats_cache.keys()) if k[0] == dataset_id and (expert_id is None or k[1] == expert_id)]
        for k in keys:
            self._stats_cache.pop(k, None)
            self._stats_cache_expiry.pop(k, None)

    def list(self) -> List[Dict[str, Any]]:
        self.ensure_db()
        data = dataset_repository.list()
        for ds in data:
            ds.setdefault('multi_select', False)
        return data

    def statistics(self, dataset_id: int, expert_id: Optional[str]) -> Dict[str, int]:
        self.ensure_db()
        cached = self._cache_get_stats(dataset_id, expert_id)
        if cached:
            return cached  # type: ignore
        # repository direct statistics until migrated fully
        total_count = self.db.image_datasets.count_documents({"dataset_id": dataset_id})
        annotated_count = self.db.annotations.count_documents({
            "dataset_id": dataset_id,
            "expert_id": expert_id
        }) if expert_id else 0
        result = {"total_count": total_count, "annotated_count": annotated_count}
        self._cache_set_stats(dataset_id, expert_id, result)
        return result

    def create(self, name: str, description: str = '', multi_select: bool = False) -> int:
        self.ensure_db()
        dataset_id = dataset_repository.create(name, description, multi_select)
        self.invalidate_stats(dataset_id)
        return dataset_id

    def update_multi_select(self, dataset_id: int, value: bool) -> bool:
        self.ensure_db()
        ok = dataset_repository.update_multi_select(dataset_id, value)
        return ok

    def delete(self, dataset_id: int) -> int:
        self.ensure_db()
        count = dataset_repository.delete(dataset_id)
        self.invalidate_stats(dataset_id)
        return count

    def recount_images(self, dataset_id: int) -> int:
        self.ensure_db()
        actual_count = dataset_repository.recount_images(dataset_id)
        self.invalidate_stats(dataset_id)
        return actual_count

dataset_service = DatasetService()

__all__ = ["dataset_service", "DatasetService"]
