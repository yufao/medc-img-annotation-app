"""Blueprint registration aggregator for API layer (Phase 1 refactor)."""

from flask import Blueprint, jsonify
from app.core.db import USE_DATABASE, get_db

# Placeholder module exports: each sub-blueprint file will expose a `bp`.

from .auth_api import bp as auth_bp  # noqa: E402
from .dataset_api import bp as dataset_bp  # noqa: E402
from .label_api import bp as label_bp  # noqa: E402
from .image_api import bp as image_bp  # noqa: E402
from .annotation_api import bp as annotation_bp  # noqa: E402
from .export_api import bp as export_bp  # noqa: E402
from .admin_api import bp as admin_bp  # noqa: E402

def register_all(app):
    """Register all blueprints with the Flask app.
    NOTE: URL prefixes intentionally kept identical to original endpoints.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(dataset_bp)
    app.register_blueprint(label_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(annotation_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(admin_bp)
    # health check blueprint
    health_bp = Blueprint('health', __name__)
    @health_bp.route('/api/healthz', methods=['GET'])
    def healthz():
        db_ok = False
        if USE_DATABASE:
            try:
                db = get_db()
                db_ok = db is not None
            except Exception:
                db_ok = False
        return jsonify({"ok": True, "db_connected": db_ok})
    app.register_blueprint(health_bp)
