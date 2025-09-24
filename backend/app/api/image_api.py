"""Image listing & upload endpoints (Phase 2 refactored)."""
from flask import Blueprint, request, jsonify, current_app
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # compatibility if needed
from app.services.image_service import image_service  # type: ignore
from app.core.db import USE_DATABASE  # centralized flag

bp = Blueprint('images', __name__)

@bp.route('/api/admin/datasets/<int:dataset_id>/images', methods=['POST'])
def upload_dataset_images(dataset_id):
    if request.form.get('role') != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    if 'images' not in request.files:
        return jsonify({"msg": "error", "error": "没有上传图片"}), 400
    files = request.files.getlist('images')
    if not files:
        return jsonify({"msg": "error", "error": "没有选择图片"}), 400
    try:
        uploaded, failed = image_service.upload_batch(dataset_id, files)
        return jsonify({
            "msg": "success",
            "uploaded": len(uploaded),
            "failed": len(failed),
            "images": uploaded,
            "errors": failed
        }), 201
    except ValueError as ve:
        return jsonify({"msg": "error", "error": str(ve)}), 404
    except RuntimeError as re:
        return jsonify({"msg": "error", "error": str(re)}), 500
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"批量上传图片失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/datasets/<int:dataset_id>/images', methods=['GET'])
def get_dataset_images(dataset_id):
    expert_id = request.args.get('expert_id')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 20))
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    try:
        data = image_service.list_dataset_images(dataset_id, expert_id, page, page_size)
        return jsonify(data)
    except RuntimeError as re:
        return jsonify({"msg": "error", "error": str(re)}), 500
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"获取数据集图片失败: {e}")
        return jsonify([])
