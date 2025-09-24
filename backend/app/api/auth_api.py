"""Authentication related endpoints extracted from routes.py (Phase 1)."""
from flask import Blueprint, request, jsonify
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.user_config import SYSTEM_USERS as USERS  # type: ignore

bp = Blueprint('auth', __name__)

@bp.route('/api/login', methods=['POST'])
def login():  # original logic preserved
    data = request.json
    for user in USERS:
        if user['username'] == data.get('username') and user['password'] == data.get('password'):
            return jsonify({"msg": "success", "role": user['role']}), 200
    return jsonify({"msg": "fail"}), 401
