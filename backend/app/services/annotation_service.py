"""Annotation service layer (Phase 2) consolidating annotation-related operations.

Mirrors existing endpoint behaviors WITHOUT changing response shapes.

Endpoints covered:
  - images_with_annotations -> list_images_with_annotations
  - prev_image -> prev_image
  - next_image -> next_image (random unannotated)
  - annotate -> save_annotation (upsert)
  - update_annotation -> update_annotation_fields

Notes:
  * Uses linking collection image_datasets for dataset/image relationship.
  * Derives filename from image_path (since images docs store image_path only).
  * Keeps in-memory fallback lists for parity, though real DB should be primary.
"""
from __future__ import annotations
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.db import get_db, USE_DATABASE
from app.services.dataset_service import dataset_service  # for stats cache invalidation
from db_utils import get_next_annotation_id  # type: ignore


class AnnotationService:
    def __init__(self):
        self.db = get_db()
        # memory fallback (legacy compatibility)
        self.IMAGES: List[Dict[str, Any]] = []
        self.ANNOTATIONS: List[Dict[str, Any]] = []

    def ensure_db(self):
        if not USE_DATABASE or self.db is None:
            raise RuntimeError("数据库连接不可用")

    # ------------- Helpers -------------
    def _normalize_dataset_id(self, ds_id):
        if isinstance(ds_id, str) and ds_id.isdigit():
            return int(ds_id)
        return ds_id

    def _filename_from_path(self, path: str) -> str:
        return path.split('/')[-1] if path else ''

    # ------------- Listing with annotations -------------
    def list_images_with_annotations(
        self,
        dataset_id: int,
        expert_id: Optional[str],
        include_all: bool,
        page: int,
        page_size: int
    ) -> List[Dict[str, Any]]:
        self.ensure_db()
        ds_id = self._normalize_dataset_id(dataset_id)
        links = list(self.db.image_datasets.find({"dataset_id": ds_id}, {"_id": 0, "image_id": 1}))
        if not links:
            return []
        image_ids = [l['image_id'] for l in links]
        imgs = list(self.db.images.find({"image_id": {"$in": image_ids}}, {"_id": 0}))
        annotations = list(self.db.annotations.find({'dataset_id': ds_id, 'expert_id': expert_id}, {'_id': 0}))
        labels = list(self.db.labels.find({}, {"_id": 0, "label_id": 1, "label_name": 1}))
        labels_dict = {l['label_id']: l.get('label_name', '') for l in labels}
        result: List[Dict[str, Any]] = []
        for img in imgs:
            ann = next((a for a in annotations if a.get('image_id') == img.get('image_id')), None)
            if ann and ann.get('label_id'):
                ann['label_name'] = labels_dict.get(ann['label_id'], '')
            entry = {
                "image_id": img.get('image_id'),
                "filename": self._filename_from_path(img.get('image_path', '')),
                "image_path": img.get('image_path', ''),
                "annotation": ann
            }
            if include_all or not ann:
                result.append(entry)
        start = (page - 1) * page_size
        end = start + page_size
        return result[start:end]

    # ------------- Previous image -------------
    def prev_image(self, dataset_id: int, current_image_id: int) -> Dict[str, Any]:
        self.ensure_db()
        ds_id = self._normalize_dataset_id(dataset_id)
        # Prefer linking table ordering by image_id
        links = list(self.db.image_datasets.find({"dataset_id": ds_id}, {"_id": 0, "image_id": 1}))
        if not links:
            # fallback memory
            imgs = [img for img in self.IMAGES if img.get('dataset_id') == ds_id]
            imgs_sorted = sorted(imgs, key=lambda x: x.get('image_id'))
        else:
            image_ids = [l['image_id'] for l in links]
            imgs = list(self.db.images.find({"image_id": {"$in": image_ids}}, {"_id": 0}))
            imgs_sorted = sorted(imgs, key=lambda x: x.get('image_id'))
        prev_img = None
        for i, img in enumerate(imgs_sorted):
            if img.get('image_id') == current_image_id and i > 0:
                prev_img = imgs_sorted[i - 1]
                break
        if prev_img:
            # augment filename if missing
            if 'filename' not in prev_img:
                prev_img['filename'] = self._filename_from_path(prev_img.get('image_path', ''))
            return prev_img
        return {"msg": "no previous image"}

    # ------------- Next image (random unannotated) -------------
    def next_image(self, dataset_id: int, expert_id: str) -> Dict[str, Any]:
        self.ensure_db()
        ds_id = self._normalize_dataset_id(dataset_id)
        links = list(self.db.image_datasets.find({"dataset_id": ds_id}, {"_id": 0, "image_id": 1}))
        if not links:
            imgs = [img for img in self.IMAGES if img.get('dataset_id') == ds_id]
        else:
            image_ids = [l['image_id'] for l in links]
            imgs = list(self.db.images.find({"image_id": {"$in": image_ids}}, {"_id": 0}))
        for img in imgs:
            if 'image_id' not in img:
                # legacy normalization (should already exist)
                img['image_id'] = img.get('image_id')
        annotated_imgs = list(self.db.annotations.find({'dataset_id': ds_id, 'expert_id': expert_id}, {'_id': 0, 'image_id': 1}))
        if not annotated_imgs:
            annotated_imgs = [
                {'image_id': a.get('image_id')}
                for a in self.ANNOTATIONS
                if a.get('dataset_id') == ds_id and a.get('expert_id') == expert_id
            ]
        done_ids = {a.get('image_id') for a in annotated_imgs}
        untagged = [img for img in imgs if img.get('image_id') not in done_ids]
        if untagged:
            selected = random.choice(untagged)
            return {
                "image_id": selected.get('image_id'),
                "filename": selected.get('filename') or self._filename_from_path(selected.get('image_path', ''))
            }
        return {"msg": "done"}

    # ------------- Annotate / Upsert -------------
    def save_annotation(
        self,
        dataset_id: int,
        image_id: int,
        expert_id: str,
        label_id: int,
        tip: str = ''
    ) -> Dict[str, Any]:
        self.ensure_db()
        ds_id = self._normalize_dataset_id(dataset_id)
        existing = self.db.annotations.find_one({'dataset_id': ds_id, 'image_id': image_id, 'expert_id': expert_id})
        annotation_data = {
            'dataset_id': ds_id,
            'image_id': image_id,
            'expert_id': expert_id,
            'label_id': label_id,
            'datetime': datetime.now().isoformat(),
            'tip': tip
        }
        if existing:
            annotation_data['record_id'] = existing.get('record_id')
            self.db.annotations.update_one({'dataset_id': ds_id, 'image_id': image_id, 'expert_id': expert_id}, {'$set': annotation_data})
        else:
            next_record_id = get_next_annotation_id(self.db)
            annotation_data['record_id'] = next_record_id
            self.db.annotations.insert_one(annotation_data)
        # memory sync
        self.ANNOTATIONS[:] = [a for a in self.ANNOTATIONS if not (a.get('dataset_id') == ds_id and a.get('image_id') == image_id and a.get('expert_id') == expert_id)]
        memory_copy = annotation_data.copy(); memory_copy['label'] = label_id; self.ANNOTATIONS.append(memory_copy)
        # invalidate statistics cache for this (dataset, expert)
        try:
            dataset_service.invalidate_stats(ds_id, expert_id)
        except Exception:  # pragma: no cover - best effort
            pass
        return {"msg": "saved", "expert_id": expert_id}

    # ------------- Update annotation fields -------------
    def update_annotation_fields(
        self,
        dataset_id: int,
        image_id: int,
        expert_id: str,
        label_id: Optional[int],
        tip: str = ''
    ) -> Dict[str, Any]:
        self.ensure_db()
        ds_id = self._normalize_dataset_id(dataset_id)
        update_fields = {
            'label': label_id,
            'tip': tip,
            'datetime': datetime.now().isoformat()
        }
        result = self.db.annotations.update_one({'dataset_id': ds_id, 'image_id': image_id, 'expert_id': expert_id}, {'$set': update_fields})
        for ann in self.ANNOTATIONS:
            if ann.get('dataset_id') == ds_id and ann.get('image_id') == image_id and ann.get('expert_id') == expert_id:
                ann.update(update_fields)
                break
        if result.modified_count:
            try:
                dataset_service.invalidate_stats(ds_id, expert_id)
            except Exception:  # pragma: no cover
                pass
            return {"msg": "updated"}
        return {"msg": "not found or not changed"}


annotation_service = AnnotationService()

__all__ = ["annotation_service", "AnnotationService"]
