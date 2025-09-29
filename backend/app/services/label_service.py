"""Label service layer: encapsulates label CRUD and normalization logic."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from app.core.db import get_db, USE_DATABASE

class LabelService:
    def __init__(self):
        self.db = get_db()

    def ensure_db(self):
        if not USE_DATABASE or self.db is None:
            raise RuntimeError("数据库连接不可用")

    def _next_label_id_base(self) -> int:
        max_label = self.db.labels.find_one(sort=[("label_id", -1)])
        return (max_label.get('label_id', 0) + 1) if max_label else 1

    def add_dataset_labels(self, dataset_id: int, labels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.ensure_db()
        base = self._next_label_id_base()
        # 注意：pymongo 会在原地给插入的 dict 添加 _id，导致 jsonify 报 ObjectId 不可序列化
        # 这里将用于返回的 records 与实际插入的 docs 分离，避免原地突变
        records: List[Dict[str, Any]] = []  # 用于返回（无 _id）
        docs: List[Dict[str, Any]] = []     # 实际插入（可能被 pymongo 添加 _id）
        for i, label in enumerate(labels):
            doc = {
                "label_id": base + i,
                "label_name": label.get('name'),
                "category": label.get('category', '病理学'),
                "dataset_id": dataset_id
            }
            docs.append(doc)
            records.append(doc.copy())  # 拷贝一份用于返回，避免被 insert_many 原地添加 _id
        if docs:
            self.db.labels.insert_many(docs)
        return records

    def list(self, dataset_id: Optional[int]) -> List[Dict[str, Any]]:
        self.ensure_db()
        if dataset_id is not None:
            data = list(self.db.labels.find({"dataset_id": dataset_id}, {"_id": 0}))
            if not data:  # fallback to common labels
                data = list(self.db.labels.find({"dataset_id": {"$exists": False}}, {"_id": 0}))
        else:
            data = list(self.db.labels.find({}, {"_id": 0}))
        # normalize
        out = []
        for label in data:
            out.append({
                "label_id": label.get("label_id"),
                "name": label.get("name") or label.get("label_name"),
                "dataset_id": label.get("dataset_id", dataset_id)
            })
        out.sort(key=lambda x: x.get('label_id', 0))
        return out

    def get_dataset_labels(self, dataset_id: int) -> List[Dict[str, Any]]:
        self.ensure_db()
        labels = list(self.db.labels.find({"dataset_id": dataset_id}, {"_id": 0}))
        if not labels:
            labels = list(self.db.labels.find({"dataset_id": None}, {"_id": 0}))
        return labels

    def update_dataset_labels(self, dataset_id: int, labels: List[Dict[str, Any]]) -> int:
        self.ensure_db()
        self.db.labels.delete_many({"dataset_id": dataset_id})
        if not labels:
            return 0
        base = self._next_label_id_base()
        records = []
        for i, label in enumerate(labels):
            records.append({
                "label_id": base + i,
                "label_name": label.get('name'),
                "category": label.get('category', '病理学'),
                "dataset_id": dataset_id
            })
        if records:
            self.db.labels.insert_many(records)
        return len(labels)

label_service = LabelService()

__all__ = ["label_service", "LabelService"]
