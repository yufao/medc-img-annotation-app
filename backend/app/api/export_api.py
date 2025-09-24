"""Export endpoint (Phase 2 refactored)."""
from flask import Blueprint, request, jsonify, send_file, current_app
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # legacy path support
from app.services.export_service import export_service  # type: ignore
from app.core.db import USE_DATABASE

bp = Blueprint('export', __name__)

@bp.route('/api/export', methods=['GET'])
def export():
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    try:
        raw_ds = request.args.get('dataset_id')
        expert_id = request.args.get('expert_id')
        processed_ds_id = int(raw_ds) if raw_ds and raw_ds.isdigit() else None
        output = export_service.build_workbook(processed_ds_id, expert_id)
        filename = export_service.build_filename(processed_ds_id, expert_id)
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except RuntimeError as re:
        return jsonify({"msg": "error", "error": str(re)}), 500
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"通用导出失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500
