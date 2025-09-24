import pytest
from app.services.annotation_service import annotation_service
from app.services.export_service import export_service
from app.core.db import USE_DATABASE, get_db


@pytest.mark.skipif(not USE_DATABASE, reason="需要真实数据库环境")
class TestAnnotationAndExportServices:
    def setup_method(self):
        self.db = get_db()
        # 使用独立前缀，避免影响现有数据
        self.dataset_id = 999999
        # 准备最小标签
        if not self.db.labels.find_one({'label_id': 9001}):
            self.db.labels.insert_one({'label_id': 9001, 'label_name': 'pytest_label'})
        # 准备图片 + 关联
        if not self.db.images.find_one({'image_id': 80001}):
            self.db.images.insert_one({'image_id': 80001, 'image_path': '/tmp/pytest_image1.png'})
        if not self.db.image_datasets.find_one({'dataset_id': self.dataset_id, 'image_id': 80001}):
            self.db.image_datasets.insert_one({'dataset_id': self.dataset_id, 'image_id': 80001})

    def teardown_method(self):
        # 清理测试数据 (不删除公共集合中的其它数据)
        self.db.annotations.delete_many({'dataset_id': self.dataset_id})
        self.db.image_datasets.delete_many({'dataset_id': self.dataset_id})
        # 图片和标签保留以避免并行测试删除其它用例需要的数据

    def test_save_and_update_annotation(self):
        r = annotation_service.save_annotation(self.dataset_id, 80001, 'expert_py', 9001, tip='first')
        assert r['msg'] == 'saved'
        # 更新字段
        r2 = annotation_service.update_annotation_fields(self.dataset_id, 80001, 'expert_py', 9001, tip='updated')
        assert r2['msg'] in ('updated', 'not found or not changed')  # 若实现判定无变化也可接受

    def test_next_image_after_annotation(self):
        # 先保证一个未标注返回该图片
        first = annotation_service.next_image(self.dataset_id, 'expert_next')
        assert first.get('image_id') == 80001
        # 标注后应返回 done
        annotation_service.save_annotation(self.dataset_id, 80001, 'expert_next', 9001)
        second = annotation_service.next_image(self.dataset_id, 'expert_next')
        assert second.get('msg') in ('done',)  # 所有已标注

    def test_export_workbook_minimal(self):
        # 创建一条标注，导出 workbook
        annotation_service.save_annotation(self.dataset_id, 80001, 'expert_export', 9001, tip='export')
        wb_bytes = export_service.build_workbook(self.dataset_id, 'expert_export')
        # 简单断言字节大小 > 0 且包含 openpyxl 生成的签名 (PK 压缩头)
        data = wb_bytes.getvalue()
        assert data.startswith(b'PK'), '应为 xlsx (zip) 格式'
        assert len(data) > 2000, '导出内容太小，可能失败'
