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
        # 管理员导出（expert_id=admin）需要聚合所有用户
        if user_identifier and isinstance(user_identifier, str) and user_identifier.lower() == 'admin':
            user_identifier = None
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # annotations sheet
            try:
                query = {}
                if processed_ds_id is not None:
                    query['dataset_id'] = processed_ds_id
                # 管理员或未传入 expert_id 时，导出该数据集的所有用户标注
                if user_identifier is not None:
                    query['expert_id'] = user_identifier
                annotations_data = list(self.db.annotations.find(query, {"_id": 0}))
                if annotations_data:
                    for item in annotations_data:
                        if 'label' in item and 'label_id' not in item:
                            item['label_id'] = item['label']
                        item.pop('label', None)
                    # 标签按数据集过滤（无则回退全局）
                    label_query = {"dataset_id": processed_ds_id} if processed_ds_id is not None else {}
                    labels_list = list(self.db.labels.find(label_query, {"_id": 0}))
                    if processed_ds_id is not None and not labels_list:
                        labels_list = list(self.db.labels.find({"dataset_id": {"$exists": False}}, {"_id": 0})) or \
                                      list(self.db.labels.find({"dataset_id": None}, {"_id": 0}))
                    labels_dict = {l.get('label_id'): l.get('label_name', '') for l in labels_list}
                    for item in annotations_data:
                        # 多标签支持：若存在 label_ids，生成逗号分隔的名称；否则保持单标签
                        if 'label_ids' in item and isinstance(item['label_ids'], list) and item['label_ids']:
                            names = [labels_dict.get(lid, '') for lid in item['label_ids']]
                            item['label_name'] = ','.join([n for n in names if n])
                            # 为兼容旧字段，label_id 保留首个
                            if 'label_id' not in item and item['label_ids']:
                                item['label_id'] = item['label_ids'][0]
                        else:
                            item['label_name'] = labels_dict.get(item.get('label_id'), '')
                    adf = pd.DataFrame(annotations_data)
                    # 增加 label_ids 字段（多标签模式下的原始列表），导出时保持逗号分隔在 label_name 中
                    if 'label_ids' in adf.columns:
                        # 若需要可保留原列表列；当前只展示方便溯源
                        pass
                    col_order = ['dataset_id','record_id','image_id','expert_id','label_id','label_ids','label_name','tip','datetime']
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
                # 标签工作表也按数据集过滤，保持导出内容相干
                if processed_ds_id is not None:
                    labels_data = list(self.db.labels.find({"dataset_id": processed_ds_id}, {"_id": 0}))
                    if not labels_data:
                        labels_data = list(self.db.labels.find({"dataset_id": {"$exists": False}}, {"_id": 0})) or \
                                      list(self.db.labels.find({"dataset_id": None}, {"_id": 0}))
                else:
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
