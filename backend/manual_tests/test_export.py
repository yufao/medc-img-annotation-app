#!/usr/bin/env python3
"""
手工测试导出功能 - 生成 Excel 并打印工作表
"""
import os
import sys
from io import BytesIO
import pandas as pd

# backend 根目录
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app import create_app  # noqa: E402
from app.core.db import get_db  # noqa: E402

def main():
    print("=== 开始测试导出功能（手工） ===")
    app = create_app()
    with app.app_context():
        db = get_db()
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # annotations
            annotations = list(db.annotations.find({}, {"_id": 0})) if db else []
            pd.DataFrame(annotations).to_excel(writer, sheet_name='annotations', index=False)
            # images
            images = list(db.images.find({}, {"_id": 0})) if db else []
            pd.DataFrame(images).to_excel(writer, sheet_name='images', index=False)
            # labels
            labels = list(db.labels.find({}, {"_id": 0})) if db else []
            pd.DataFrame(labels).to_excel(writer, sheet_name='labels', index=False)
        output.seek(0)
        out_path = os.path.expanduser('~/test_export_result.xlsx')
        with open(out_path, 'wb') as f:
            f.write(output.getvalue())
        print(f"✅ 导出完成: {out_path}")

if __name__ == '__main__':
    main()
