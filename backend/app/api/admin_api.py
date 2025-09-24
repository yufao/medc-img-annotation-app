"""Admin related endpoints (Phase 2 service refactor)."""
from flask import Blueprint, request, jsonify
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # legacy path
from app.services.user_service import user_service  # type: ignore
from app.core.db import get_db, USE_DATABASE, MONGO_URI, MONGO_DB_NAME

bp = Blueprint('admin', __name__)

@bp.route('/api/admin/users', methods=['GET'])
def get_users():
    if request.args.get('role') != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    return jsonify(user_service.list_users())

@bp.route('/api/admin/users/config', methods=['GET'])
def get_user_config_info():
    if request.args.get('role') != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    return jsonify(user_service.config_info())

@bp.route('/api/admin/db_status', methods=['GET'])
def db_status():
    if request.args.get('role') != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    db = get_db()
    if not USE_DATABASE or db is None:
        return jsonify({
            "connected": False,
            "mongo_uri": MONGO_URI,
            "db_name": MONGO_DB_NAME,
            "message": "数据库未连接"
        }), 200
    # 选取核心集合统计（存在才统计）
    core_collections = ["datasets", "images", "image_datasets", "annotations", "labels", "sequences"]
    counts = {}
    for c in core_collections:
        if c in db.list_collection_names():
            counts[c] = db[c].count_documents({})
    return jsonify({
        "connected": True,
        "mongo_uri": MONGO_URI,
        "db_name": MONGO_DB_NAME,
        "collections": counts
    })

@bp.route('/api/debug/db', methods=['GET'])
def debug_db():
    db = get_db()
    state = {
        "use_database_flag": USE_DATABASE,
        "mongo_uri": MONGO_URI,
        "db_name": MONGO_DB_NAME,
        "connected": bool(USE_DATABASE and db is not None),
    }
    if USE_DATABASE and db is not None:
        names = db.list_collection_names()
        primary = [c for c in ["datasets","images","image_datasets","annotations","labels","sequences","system_info"] if c in names]
        counts = {c: db[c].count_documents({}) for c in primary}
        state["collections"] = counts
    return jsonify(state)
