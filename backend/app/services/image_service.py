"""Image service layer: handles image upload and listing (Phase 2).

Responsibilities:
  * Batch upload images into storage folder
  * Maintain images collection + image_datasets relation
  * Provide paginated listing with (optional) expert annotations merged
  * Enrich annotation with label_name via labels cache

NOTE: Keeps behavior & response fields identical to original image_api endpoints.
"""
from __future__ import annotations
import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.core.db import get_db, USE_DATABASE
from db_utils import get_next_sequence_value  # type: ignore
from config import UPLOAD_FOLDER  # type: ignore

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class ImageService:
    def __init__(self):
        self.db = get_db()

    def ensure_db(self):
        if not USE_DATABASE or self.db is None:
            raise RuntimeError("数据库连接不可用")

    # ---------------- Upload -----------------
    def upload_batch(self, dataset_id: int, files: List[FileStorage]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Save multiple images; return (uploaded, failed).

        Each uploaded record: {image_id, filename, original_name}
        Each failed record: {filename, error}
        """
        self.ensure_db()
        dataset = self.db.datasets.find_one({"id": dataset_id})
        if not dataset:
            raise ValueError(f"数据集 {dataset_id} 不存在")
        uploaded: List[Dict[str, Any]] = []
        failed: List[Dict[str, Any]] = []
        for file in files:
            if not file or not file.filename:
                continue
            original_filename = secure_filename(file.filename)
            filename = f"{uuid.uuid4().hex}_{original_filename}"
            try:
                path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(path)
                image_id = get_next_sequence_value(self.db, "images_id")
                self.db.images.insert_one({"image_id": image_id, "image_path": f"static/img/{filename}"})
                self.db.image_datasets.insert_one({"image_id": image_id, "dataset_id": dataset_id})
                uploaded.append({
                    "image_id": image_id,
                    "filename": filename,
                    "original_name": original_filename
                })
            except Exception as e:  # pragma: no cover (per-file errors)
                failed.append({"filename": file.filename, "error": str(e)})
        if uploaded:
            self.db.datasets.update_one({"id": dataset_id}, {"$inc": {"image_count": len(uploaded)}})
        return uploaded, failed

    # ---------------- Listing -----------------
    def list_dataset_images(
        self,
        dataset_id: int,
        expert_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        self.ensure_db()
        links = list(self.db.image_datasets.find({"dataset_id": dataset_id}, {"_id": 0, "image_id": 1}))
        if not links:
            return []
        image_ids = [l['image_id'] for l in links]
        imgs = list(self.db.images.find({"image_id": {"$in": image_ids}}, {"_id": 0}))
        annotations = list(self.db.annotations.find({'dataset_id': dataset_id, 'expert_id': expert_id}, {'_id': 0})) if expert_id else []
        # 标签按数据集过滤，若该数据集没有专属标签，则回退到全局标签
        labels = list(self.db.labels.find({"dataset_id": dataset_id}, {"_id": 0, "label_id": 1, "label_name": 1}))
        if not labels:
            labels = list(self.db.labels.find({"dataset_id": {"$exists": False}}, {"_id": 0, "label_id": 1, "label_name": 1})) or \
                     list(self.db.labels.find({"dataset_id": None}, {"_id": 0, "label_id": 1, "label_name": 1}))
        labels_dict = {l['label_id']: l.get('label_name', '') for l in labels}
        result: List[Dict[str, Any]] = []
        for img in imgs:
            ann = next((a for a in annotations if a.get('image_id') == img.get('image_id')), None)
            if ann and ann.get('label_id'):
                ann['label_name'] = labels_dict.get(ann['label_id'], '')
                ann['label'] = ann.get('label_id')  # 兼容字段
            result.append({
                "image_id": img.get('image_id'),
                "filename": img.get('image_path', '').split('/')[-1],
                "image_path": img.get('image_path', ''),
                "annotation": ann
            })
        start, end = (page - 1) * page_size, (page - 1) * page_size + page_size
        return result[start:end]


image_service = ImageService()

__all__ = ["image_service", "ImageService"]
