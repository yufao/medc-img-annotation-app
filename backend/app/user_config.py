"""
用户管理配置文件
管理员可以通过修改此文件来管理系统用户
修改后需要重启后端服务才能生效
"""

# 系统用户配置
# 格式：{"username": "用户名", "password": "密码", "role": "角色", "description": "用户描述"}
# 角色类型：admin（管理员）、doctor（医生）、student（学生）
SYSTEM_USERS = [
    {
        "username": "admin",
        "password": "admin123", 
        "role": "admin",
        "description": "系统管理员 - 拥有所有权限"
    },

    {
        "username": "dtr001", 
        "password": "fst222",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr002", 
        "password": "secd113",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr003", 
        "password": "thrd332",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr004", 
        "password": "455frth",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr005", 
        "password": "554fif",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr006", 
        "password": "sx666",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr007", 
        "password": "seve77",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr008", 
        "password": "eit888",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr009", 
        "password": "996nine",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },
    {
        "username": "dtr010", 
        "password": "te1010",
        "role": "doctor",
        "description": "医生 - 可进行专业标注"
    },

    {
        "username": "student",
        "password": "student123", 
        "role": "student",
        "description": "学生 - 学习标注"
    }
]

# 用户角色到expert_id的映射（不要修改）
ROLE_TO_EXPERT_ID = {
    "admin": 0,    # 管理员标注作为真实标签
    "doctor": 1,   # 医生标注
    "student": 2   # 学生标注
}

# 用户管理说明：
# 1. 添加新用户：在SYSTEM_USERS列表中添加新的用户字典
# 2. 删除用户：从SYSTEM_USERS列表中移除对应的用户字典
# 3. 修改密码：更改对应用户的password字段
# 4. 修改角色：更改对应用户的role字段（必须是admin/doctor/student之一）
# 5. 所有修改后需要重启后端服务才能生效
# 
# 注意：
# - username必须唯一
# - role必须是admin/doctor/student之一
# - password建议使用强密码
# - 不建议删除admin用户，除非确保有其他管理员账户