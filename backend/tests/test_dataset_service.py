import pytest
from app.services.dataset_service import dataset_service
from app.core.db import get_db, USE_DATABASE

@pytest.mark.skipif(not USE_DATABASE, reason="需要真实数据库环境")
class TestDatasetService:
    def test_create_and_list_with_multi_select(self):
        name = "pytest_ds_multi_select"
        ds_id = dataset_service.create(name, "desc", multi_select=True)
        datasets = dataset_service.list()
        matched = [d for d in datasets if d['id'] == ds_id]
        assert matched, "创建后应能在列表中找到数据集"
        assert matched[0].get('multi_select') is True

    def test_update_multi_select(self):
        ds_id = dataset_service.create("pytest_ds_update", "desc", multi_select=False)
        ok = dataset_service.update_multi_select(ds_id, True)
        assert ok is True
        # 验证
        datasets = dataset_service.list()
        updated = [d for d in datasets if d['id'] == ds_id][0]
        assert updated['multi_select'] is True
