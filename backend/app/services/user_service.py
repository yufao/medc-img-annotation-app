"""User service: wraps static config-based user management (Phase 2)."""
from __future__ import annotations
from typing import List, Dict, Any
from app.user_config import SYSTEM_USERS as USERS, ROLE_TO_EXPERT_ID  # type: ignore


class UserService:
    def list_users(self) -> List[Dict[str, Any]]:
        return [
            {
                "username": u.get("username"),
                "role": u.get("role"),
                "description": u.get("description", "")
            } for u in USERS
        ]

    def config_info(self) -> Dict[str, Any]:
        return {
            "message": "用户管理采用配置文件方式",
            "config_file": "backend/app/user_config.py",
            "instructions": [
                "1. 修改 backend/app/user_config.py 文件中的 SYSTEM_USERS 配置",
                "2. 可以添加、删除或修改用户信息",
                "3. 修改后需要重启后端服务才能生效",
                "4. 用户角色支持：admin（管理员）、doctor（医生）、student（学生）",
                "5. 建议为用户设置强密码"
            ],
            "current_users_count": len(USERS),
            "roles_mapping": dict(ROLE_TO_EXPERT_ID)
        }


user_service = UserService()

__all__ = ["user_service", "UserService"]
