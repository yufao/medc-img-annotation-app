"""Dataset repository encapsulating raw MongoDB access.

Narrow interface intentionally – service layer owns orchestration & caching.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.db import get_db, USE_DATABASE
from db_utils import get_next_sequence_value  # type: ignore


class DatasetRepository:
    def __init__(self):
        self.db = get_db()

    def _ensure(self):
        if self.db is None or not USE_DATABASE:
            self.db = get_db()
        if not USE_DATABASE or self.db is None:
            raise RuntimeError("数据库连接不可用")

    # --- Queries ---
    def list(self) -> List[Dict[str, Any]]:
        self._ensure()
        return list(self.db.datasets.find({}, {'_id': 0}))

    def find_one(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        self._ensure()
        return self.db.datasets.find_one({'id': dataset_id}, {'_id': 0})

    # --- Mutations ---
    def create(self, name: str, description: str, multi_select: bool) -> int:
        self._ensure()
        next_id = get_next_sequence_value(self.db, "datasets_id")
        doc = {
            'id': next_id,
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'image_count': 0,
            'status': 'active',
            'multi_select': bool(multi_select)
        }
        self.db.datasets.insert_one(doc)
        return next_id

    def update_multi_select(self, dataset_id: int, value: bool) -> bool:
        self._ensure()
        res = self.db.datasets.update_one({'id': dataset_id}, {'$set': {'multi_select': bool(value)}})
        return res.matched_count > 0

    def delete(self, dataset_id: int) -> int:
        self._ensure()
        links = list(self.db.image_datasets.find({'dataset_id': dataset_id}, {'_id': 0, 'image_id': 1}))
        image_ids = [l['image_id'] for l in links]
        self.db.datasets.delete_one({'id': dataset_id})
        self.db.image_datasets.delete_many({'dataset_id': dataset_id})
        self.db.annotations.delete_many({'dataset_id': dataset_id})
        return len(image_ids)

    def recount_images(self, dataset_id: int) -> int:
        self._ensure()
        actual = self.db.image_datasets.count_documents({'dataset_id': dataset_id})
        self.db.datasets.update_one({'id': dataset_id}, {'$set': {'image_count': actual}})
        return actual

    # --- Statistics ---
    def statistics(self, dataset_id: int, expert_id: Optional[str]) -> Dict[str, int]:
        self._ensure()
        total = self.db.image_datasets.count_documents({'dataset_id': dataset_id})
        annotated = self.db.annotations.count_documents({'dataset_id': dataset_id, 'expert_id': expert_id}) if expert_id else 0
        return {'total_count': total, 'annotated_count': annotated}


dataset_repository = DatasetRepository()

__all__ = ['dataset_repository', 'DatasetRepository']
