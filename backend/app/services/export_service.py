"""Export service layer: builds Excel workbook in-memory (Phase 2)."""
from __future__ import annotations
from datetime import datetime
from io import BytesIO
from typing import Optional
import pandas as pd

from app.core.db import get_db, USE_DATABASE


class ExportService:
    def __init__(self):
        self.db = get_db()

    def ensure_db(self):
        if not USE_DATABASE or self.db is None:
            raise RuntimeError("数据库连接不可用")

    def build_workbook(self, dataset_id: Optional[int], expert_id: Optional[str]) -> BytesIO:
        """Construct an Excel workbook identical to previous logic; returns BytesIO ready for download."""
        self.ensure_db()
        output = BytesIO()
        processed_ds_id = dataset_id
        user_identifier = expert_id if expert_id else None
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # annotations sheet
            try:
                query = {}
                if processed_ds_id is not None:
                    query['dataset_id'] = processed_ds_id
                if user_identifier is not None:
                    query['expert_id'] = user_identifier
                annotations_data = list(self.db.annotations.find(query, {"_id": 0}))
                if annotations_data:
                    for item in annotations_data:
                        if 'label' in item and 'label_id' not in item:
                            item['label_id'] = item['label']
                        item.pop('label', None)
                    labels_dict = {l.get('label_id'): l.get('label_name', '') for l in self.db.labels.find({}, {"_id": 0})}
                    for item in annotations_data:
                        item['label_name'] = labels_dict.get(item.get('label_id'), '')
                    adf = pd.DataFrame(annotations_data)
                    col_order = ['dataset_id','record_id','image_id','expert_id','label_id','label_name','tip','datetime']
                    adf = adf.reindex(columns=[c for c in col_order if c in adf.columns])
                    if 'dataset_id' in adf.columns:
                        adf = adf.sort_values(['dataset_id','record_id'])
                    sheet = f"数据集{processed_ds_id}标注" if processed_ds_id else '标注数据'
                    adf.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    empty = pd.DataFrame(columns=['dataset_id','record_id','image_id','expert_id','label_id','label_name','tip','datetime'])
                    sheet = f"数据集{processed_ds_id}标注" if processed_ds_id else '标注数据'
                    empty.to_excel(writer, sheet_name=sheet, index=False)
            except Exception as e:  # pragma: no cover - captured into sheet
                pd.DataFrame([{'error': str(e)}]).to_excel(writer, sheet_name='标注数据错误', index=False)
            # images sheet
            try:
                img_query = {}
                if processed_ds_id is not None:
                    links = list(self.db.image_datasets.find({"dataset_id": processed_ds_id}, {"_id": 0, "image_id": 1}))
                    if links:
                        img_query['image_id'] = {"$in": [l['image_id'] for l in links]}
                images_data = list(self.db.images.find(img_query, {"_id": 0}))
                idf = pd.DataFrame(images_data) if images_data else pd.DataFrame(columns=['image_id','image_path'])
                idf = idf.reindex(columns=[c for c in ['image_id','image_path'] if c in idf.columns])
                sheet = f"数据集{processed_ds_id}图片" if processed_ds_id else '图片数据'
                idf.to_excel(writer, sheet_name=sheet, index=False)
            except Exception as e:  # pragma: no cover
                pd.DataFrame([{'error': str(e)}]).to_excel(writer, sheet_name='图片数据错误', index=False)
            # labels sheet
            try:
                labels_data = list(self.db.labels.find({}, {"_id": 0}))
                ldf = pd.DataFrame(labels_data) if labels_data else pd.DataFrame(columns=['label_id','label_name','category'])
                if not ldf.empty and 'label_id' in ldf.columns:
                    ldf = ldf.sort_values('label_id')
                ldf = ldf.reindex(columns=[c for c in ['label_id','label_name','category'] if c in ldf.columns])
                sheet = f"数据集{processed_ds_id}标签" if processed_ds_id else '标签数据'
                ldf.to_excel(writer, sheet_name=sheet, index=False)
            except Exception as e:  # pragma: no cover
                pd.DataFrame([{'error': str(e)}]).to_excel(writer, sheet_name='标签数据错误', index=False)
            # datasets sheet
            try:
                ds_query = { 'id': processed_ds_id } if processed_ds_id is not None else {}
                ds_data = list(self.db.datasets.find(ds_query, {"_id": 0}))
                ddf = pd.DataFrame(ds_data) if ds_data else pd.DataFrame(columns=['id','name','description','created_at','image_count','status'])
                ddf = ddf.reindex(columns=[c for c in ['id','name','description','created_at','image_count','status'] if c in ddf.columns])
                ddf.to_excel(writer, sheet_name='数据集信息', index=False)
            except Exception as e:  # pragma: no cover
                pd.DataFrame([{'error': str(e)}]).to_excel(writer, sheet_name='数据集信息错误', index=False)
        output.seek(0)
        return output

    def build_filename(self, dataset_id: Optional[int], expert_id: Optional[str]) -> str:
        base = "医学图像标注数据"
        if dataset_id:
            base += f"_数据集{dataset_id}"
        if expert_id:
            base += f"_{expert_id}"
        base += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return base


export_service = ExportService()

__all__ = ["export_service", "ExportService"]
