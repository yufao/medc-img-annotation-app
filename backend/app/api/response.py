"""Unified API response helpers & error classes (Phase 3)."""
from __future__ import annotations
from typing import Any, Dict, Optional
from flask import jsonify


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = 'error', payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.payload = payload or {}

    def to_dict(self) -> Dict[str, Any]:
        data = {'code': self.code, 'message': self.message}
        if self.payload:
            data['details'] = self.payload
        return data


def success(data: Any = None, message: str = 'success', code: str = 'ok', status: int = 200):
    body = {'code': code, 'message': message}
    if data is not None:
        body['data'] = data
    return jsonify(body), status


def fail(message: str, status: int = 400, code: str = 'error', details: Optional[Dict[str, Any]] = None):
    body = {'code': code, 'message': message}
    if details:
        body['details'] = details
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def _handle_api_error(err: ApiError):  # pragma: no cover - trivial wrapper
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(404)
    def _not_found(e):  # pragma: no cover
        return fail('资源未找到', 404, code='not_found')

    @app.errorhandler(500)
    def _internal(e):  # pragma: no cover
        return fail('服务器内部错误', 500, code='internal_error')

__all__ = ['ApiError', 'success', 'fail', 'register_error_handlers']
