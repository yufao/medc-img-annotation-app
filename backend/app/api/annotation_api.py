"""Annotation related endpoints (Phase 2 refactored to service layer)."""
from flask import Blueprint, request, jsonify, current_app
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # legacy path support
from app.services.annotation_service import annotation_service  # type: ignore
from app.core.db import USE_DATABASE

bp = Blueprint('annotations', __name__)

@bp.route('/api/images_with_annotations', methods=['POST'])
def images_with_annotations():
    data = request.json or {}
    ds_id = data.get('dataset_id')
    expert_id = data.get('expert_id')
    include_all = data.get('include_all', False)
    page = data.get('page', 1)
    page_size = data.get('pageSize', 20)
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    try:
        result = annotation_service.list_images_with_annotations(ds_id, expert_id, include_all, page, page_size)
        return jsonify(result)
    except RuntimeError as re:
        return jsonify({"msg": "error", "error": str(re)}), 500
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"获取图片标注失败: {e}")
        return jsonify([])

@bp.route('/api/prev_image', methods=['POST'])
def prev_image():
    data = request.json or {}
    ds_id = data.get('dataset_id')
    curr_image_id = data.get('image_id') or data.get('current_image_id')
    expert_id = data.get('expert_id')
    by = data.get('by', 'last_annotated')
    try:
        result = annotation_service.prev_image(ds_id, curr_image_id, expert_id=expert_id, by=by)
        return jsonify(result)
    except RuntimeError as re:
        return jsonify({"msg": "error", "error": str(re)})
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"获取上一张图片失败: {e}")
        return jsonify({"msg": "error"})

@bp.route('/api/next_image', methods=['POST'])
def next_image():
    data = request.json or {}
    ds_id = data.get('dataset_id')
    expert_id = data.get('expert_id')
    try:
        result = annotation_service.next_image(ds_id, expert_id)
        return jsonify(result)
    except RuntimeError as re:
        return jsonify({"msg": "error", "error": str(re)})
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"获取下一张图片失败: {e}")
        return jsonify({"msg": "error"})

@bp.route('/api/annotate', methods=['POST'])
def annotate():
    data = request.json or {}
    ds_id = data.get('dataset_id')
    image_id = data.get('image_id')
    expert_id = data.get('expert_id')
    label = data.get('label')  # 单标签兼容
    label_ids = data.get('label_ids')  # 多标签（新）
    tip = data.get('tip', '')
    try:
        result = annotation_service.save_annotation(ds_id, image_id, expert_id, label, tip, label_ids=label_ids)
        return jsonify(result)
    except RuntimeError as re:
        return jsonify({"msg": "error", "error": str(re)})
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"保存标注失败: {e}")
        return jsonify({"msg": "error", "error": str(e)})

@bp.route('/api/update_annotation', methods=['POST'])
def update_annotation():
    data = request.json or {}
    ds_id = data.get('dataset_id')
    image_id = data.get('image_id')
    expert_id = data.get('expert_id')
    label = data.get('label')
    label_ids = data.get('label_ids')
    tip = data.get('tip', '')
    try:
        result = annotation_service.update_annotation_fields(ds_id, image_id, expert_id, label, tip, label_ids=label_ids)
        return jsonify(result)
    except RuntimeError as re:
        return jsonify({"msg": "error", "error": str(re)})
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"更新标注失败: {e}")
        return jsonify({"msg": "error"})
