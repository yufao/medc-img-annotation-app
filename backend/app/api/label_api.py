"""Label management endpoints (Phase 2 refactored to service)."""
from flask import Blueprint, request, jsonify, current_app
from app.services.label_service import label_service
from app.core.db import USE_DATABASE

bp = Blueprint('labels', __name__)

@bp.route('/api/admin/datasets/<int:dataset_id>/labels', methods=['POST'])
def add_dataset_labels(dataset_id):
    data = request.json
    if data.get('role') != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    labels_req = data.get('labels', [])
    if not labels_req:
        return jsonify({"msg": "error", "error": "标签列表不能为空"}), 400
    try:
        records = label_service.add_dataset_labels(dataset_id, labels_req)
        return jsonify({"msg": "success", "added_labels": len(records), "labels": records}), 201
    except Exception as e:
        current_app.logger.error(f"添加标签失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/labels', methods=['GET'])
def get_labels():
    ds_id = request.args.get('dataset_id')
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    try:
        processed = int(ds_id) if ds_id and ds_id.isdigit() else None
        data = label_service.list(processed)
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"获取标签失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/admin/datasets/<int:dataset_id>/labels', methods=['GET'])
def get_dataset_labels(dataset_id):
    if request.args.get('role') != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    try:
        labels = label_service.get_dataset_labels(dataset_id)
        return jsonify(labels)
    except Exception as e:
        current_app.logger.error(f"获取数据集标签失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/admin/datasets/<int:dataset_id>/labels', methods=['PUT'])
def update_dataset_labels(dataset_id):
    data = request.json
    if data.get('role') != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    labels_req = data.get('labels', [])
    try:
        updated = label_service.update_dataset_labels(dataset_id, labels_req)
        return jsonify({"msg": "success", "updated_labels": updated})
    except Exception as e:
        current_app.logger.error(f"更新标签失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500
