"""Dataset related endpoints (Phase 2 refactored to service, Phase 3 unified response)."""
from flask import Blueprint, request, current_app
from app.services.dataset_service import dataset_service
from app.core.db import USE_DATABASE
from app.api.response import success, fail, ApiError

bp = Blueprint('datasets', __name__)

@bp.route('/api/datasets', methods=['GET'])
def get_datasets():
    if not USE_DATABASE:
        return fail("数据库连接不可用", 500)
    data = dataset_service.list()
    current_app.logger.info(f"获取到 {len(data)} 个数据集")
    return success(data)

@bp.route('/api/datasets/<int:dataset_id>/statistics', methods=['GET'])
def get_dataset_statistics(dataset_id):
    expert_id = request.args.get('expert_id')
    if not USE_DATABASE:
        return fail("数据库连接不可用", 500)
    stats = dataset_service.statistics(dataset_id, expert_id)
    return success(stats)

@bp.route('/api/admin/datasets', methods=['POST'])
def create_dataset():
    data = request.json or {}
    if data.get('role') != 'admin':
        return fail("权限不足", 403, code='forbidden')
    if not USE_DATABASE:
        return fail("数据库连接不可用", 500)
    name = data.get('name')
    if not name:
        return fail("数据集名称不能为空", 400, code='invalid_param')
    ds_id = dataset_service.create(
        name,
        data.get('description', ''),
        data.get('multi_select', False)
    )
    return success({"dataset_id": ds_id}, status=201)

@bp.route('/api/admin/datasets/<int:dataset_id>/multi-select', methods=['PATCH'])
def update_dataset_multi_select(dataset_id):
    data = request.json or {}
    if data.get('role') != 'admin':
        return fail("权限不足", 403, code='forbidden')
    if not USE_DATABASE:
        return fail("数据库连接不可用", 500)
    if 'multi_select' not in data:
        return fail("缺少 multi_select 字段", 400, code='invalid_param')
    updated = dataset_service.update_multi_select(dataset_id, data.get('multi_select'))
    if not updated:
        return fail("数据集不存在", 404, code='not_found')
    return success({"dataset_id": dataset_id, "multi_select": bool(data.get('multi_select'))})

@bp.route('/api/admin/datasets/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    if request.args.get('role') != 'admin':
        return fail("权限不足", 403, code='forbidden')
    if not USE_DATABASE:
        return fail("数据库连接不可用", 500)
    deleted_images = dataset_service.delete(dataset_id)
    return success({"deleted_images": deleted_images})

@bp.route('/api/admin/datasets/<int:dataset_id>/recount', methods=['POST'])
def recount_dataset_images(dataset_id):
    if (request.json or {}).get('role') != 'admin':
        return fail("权限不足", 403, code='forbidden')
    if not USE_DATABASE:
        return fail("数据库连接不可用", 500)
    count = dataset_service.recount_images(dataset_id)
    return success({"dataset_id": dataset_id, "image_count": count})
