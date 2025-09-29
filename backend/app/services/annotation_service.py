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
        """列出数据集图片并合并（可选）某专家的标注信息。

        参数：
        - dataset_id: 数据集 ID
        - expert_id: 专家标识（用户名/账号），用于合并该用户的标注并生成稳定随机顺序
        - include_all: 是否包含已标注图片；False 时仅返回未标注子集
        - page, page_size: 分页参数

        返回：
        - 列表，每项包含 {image_id, filename, image_path, annotation?}
          其中 annotation 内兼容字段：label_id 与 label（历史字段）

        说明：
        - 未标注子集会根据“(dataset_id, expert_id)”生成稳定随机顺序；
        - 当 include_all=True 时，返回“未标注(随机) + 已标注(后)”。
        """
        self.ensure_db()
        ds_id = self._normalize_dataset_id(dataset_id)
        links = list(self.db.image_datasets.find({"dataset_id": ds_id}, {"_id": 0, "image_id": 1}))
        if not links:
            return []
        image_ids = [l['image_id'] for l in links]
        imgs = list(self.db.images.find({"image_id": {"$in": image_ids}}, {"_id": 0}))
        annotations = list(self.db.annotations.find({'dataset_id': ds_id, 'expert_id': expert_id}, {'_id': 0}))
        # 标签按数据集过滤，若该数据集没有专属标签，则回退到全局标签（dataset_id 缺失或为 None）
        labels = list(self.db.labels.find({"dataset_id": ds_id}, {"_id": 0, "label_id": 1, "label_name": 1}))
        if not labels:
            labels = list(self.db.labels.find({"dataset_id": {"$exists": False}}, {"_id": 0, "label_id": 1, "label_name": 1})) or \
                     list(self.db.labels.find({"dataset_id": None}, {"_id": 0, "label_id": 1, "label_name": 1}))
        labels_dict = {l['label_id']: l.get('label_name', '') for l in labels}
        result: List[Dict[str, Any]] = []
        for img in imgs:
            ann = next((a for a in annotations if a.get('image_id') == img.get('image_id')), None)
            if ann and ann.get('label_id'):
                ann['label_name'] = labels_dict.get(ann['label_id'], '')
                # 兼容前端沿用的字段名 'label'
                ann['label'] = ann.get('label_id')
            entry = {
                "image_id": img.get('image_id'),
                "filename": self._filename_from_path(img.get('image_path', '')),
                "image_path": img.get('image_path', ''),
                "annotation": ann
            }
            if include_all or not ann:
                result.append(entry)
        # 使用“用户+数据集”的稳定随机顺序重排未标注项
        if expert_id:
            try:
                import hashlib
                seed_src = f"{ds_id}:{expert_id}"
                seed_int = int(hashlib.md5(seed_src.encode('utf-8')).hexdigest(), 16) % (2**31)
                rng = random.Random(seed_int)
                untagged = [r for r in result if not r.get('annotation')]
                tagged = [r for r in result if r.get('annotation')]
                if untagged:
                    # 关键修正：先对“全部图片ID”进行一次稳定随机，再按该全局顺序对子集排序
                    all_ids = [img.get('image_id') for img in imgs]
                    rng.shuffle(all_ids)
                    order_index = {img_id: i for i, img_id in enumerate(all_ids)}
                    untagged.sort(key=lambda r: order_index.get(r['image_id'], 0))
                    # include_all=False 时只返回未标注；True 时先未标注后已标注
                    result = untagged if not include_all else (untagged + tagged)
            except Exception:
                # 失败则保持原顺序
                pass
        start = (page - 1) * page_size
        end = start + page_size
        return result[start:end]

    # ------------- Previous image -------------
    def prev_image(self, dataset_id: int, current_image_id: int) -> Dict[str, Any]:
        """获取上一张图片（按 image_id 升序的前一个）。

        返回：{image_id, filename}?；若不存在返回 {msg: 'no previous image'}。
        """
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
        """获取下一张未标注图片（稳定随机顺序）。

        策略：以 (dataset_id, expert_id) 作为种子，对数据集图片 ID 进行伪随机打乱，
        返回顺序中第一个尚未被该用户标注的图片；若全部标注完成返回 {msg: 'done'}。
        """
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
            # 使用“用户+数据集”的稳定随机顺序，返回第一个未标注项
            try:
                import hashlib
                seed_src = f"{ds_id}:{expert_id}"
                seed_int = int(hashlib.md5(seed_src.encode('utf-8')).hexdigest(), 16) % (2**31)
                rng = random.Random(seed_int)
                id_list = [img.get('image_id') for img in imgs]
                rng.shuffle(id_list)
                # 找到顺序中第一个尚未标注的 image_id
                pick_id = next((iid for iid in id_list if iid not in done_ids), None)
                if pick_id is not None:
                    selected = next((img for img in imgs if img.get('image_id') == pick_id), untagged[0])
                else:
                    selected = untagged[0]
            except Exception:
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
        """保存/更新单条标注（单选模式）。

        行为：
        - upsert：同 (dataset_id, image_id, expert_id) 若已存在则更新，否则插入新纪录；
        - 维护 record_id 自增序列；
        - 写入 label_id 并兼容内存副本中的历史字段 label；
        - 触发数据集统计缓存失效。
        返回：{"msg": "saved", "expert_id": expert_id}
        """
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
        """更新已存在标注的字段（label_id/tip/datetime）。

        返回：{"msg": "updated"} 或 {"msg": "not found or not changed"}
        """
        self.ensure_db()
        ds_id = self._normalize_dataset_id(dataset_id)
        update_fields = {
            'label_id': label_id,
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
