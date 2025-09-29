"""Pytest 配置：确保可以从 tests 中导入 `app.*` 模块。

将仓库中的 `backend` 目录加入 sys.path，这样 `from app.services...` 能正常解析。
"""
import os
import sys

_HERE = os.path.dirname(__file__)
_BACKEND_DIR = os.path.abspath(os.path.join(_HERE, ".."))  # 指向 backend 目录

if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
