"""Centralized database access utilities (Phase 2).

Provides:
    get_client() -> MongoClient or None
    get_db() -> database object or None
    USE_DATABASE: bool flag

Later phases can extend with lazy init, connection pooling metrics, or
memory backend selection.
"""
from __future__ import annotations
import os
from typing import Optional
from pymongo import MongoClient
from dotenv import load_dotenv

# 确保在读取环境变量前加载 .env
load_dotenv()

# Environment variable fallbacks align with existing config usage
# 优先顺序：显式 MONGO_URI / MONGO_DB -> 兼容旧变量 MONGODB_URI / MONGODB_DB -> 默认值（与 config.py 默认保持一致）
MONGO_URI = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI') or 'mongodb://localhost:27017/'
MONGO_DB_NAME = os.getenv('MONGO_DB') or os.getenv('MONGODB_DB') or 'medical_annotation'

_client: Optional[MongoClient] = None
USE_DATABASE = False

def _init(force: bool = False):
    global _client, USE_DATABASE
    if _client is not None and not force:
        return
    try:
        c = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
        c.server_info()  # trigger connection
        _client = c
        USE_DATABASE = True
        print(f"[core.db] ✅ Connected {MONGO_URI} -> {MONGO_DB_NAME}")
    except Exception as e:  # pragma: no cover
        print(f"[core.db] ❌ DB unavailable: {e}")
        _client = None
        USE_DATABASE = False

def get_client() -> Optional[MongoClient]:
    if _client is None:
        _init()
    return _client

def get_db():
    # 若之前初始化失败，使用懒重试策略（第一次失败后每次调用再尝试一次）
    if not USE_DATABASE:
        _init(force=True)
    client = get_client()
    if not client:
        return None
    return client[MONGO_DB_NAME]

def is_db_connected() -> bool:
    """返回当前数据库是否已连接（动态检测）。"""
    return get_client() is not None

# 在模块导入阶段主动初始化一次，避免其它模块在首次导入时看到默认 False 并缓存
try:  # pragma: no cover - 连接成功/失败路径在运行时验证
    _init()
except Exception:
    pass

__all__ = ["get_client", "get_db", "USE_DATABASE", "MONGO_URI", "MONGO_DB_NAME", "is_db_connected"]
