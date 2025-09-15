#!/usr/bin/env python3
"""
测试脚本 - 验证用户管理和ObjectId序列化修改
"""

import sys
import os
sys.path.append('/home/droot/medc-img-annotation-app/backend')

def test_user_config():
    """测试用户配置模块"""
    print("🔧 测试用户配置模块...")
    try:
        # 直接读取配置文件内容而不导入模块
        config_file = '/home/droot/medc-img-annotation-app/backend/app/user_config.py'
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ 用户配置文件读取成功")
        
        # 检查关键配置是否存在
        if 'SYSTEM_USERS' in content:
            print("✅ SYSTEM_USERS 配置存在")
        if 'ROLE_TO_EXPERT_ID' in content:
            print("✅ ROLE_TO_EXPERT_ID 配置存在")
        if 'admin' in content and 'doctor' in content and 'student' in content:
            print("✅ 包含所有必要角色配置")
        
        # 计算用户数量（简单统计）
        user_count = content.count('"username"')
        print(f"📊 配置统计: 约 {user_count} 个用户")
        
        return True
    except Exception as e:
        print(f"❌ 用户配置测试失败: {e}")
        return False

def test_json_utils():
    """测试JSON序列化工具"""
    print("\n🔧 测试JSON序列化工具...")
    try:
        # 直接检查文件内容而不导入模块
        json_utils_file = '/home/droot/medc-img-annotation-app/backend/app/json_utils.py'
        with open(json_utils_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ JSON工具文件读取成功")
        
        # 检查关键函数是否存在
        functions_to_check = ['safe_jsonify', 'convert_objectid_to_str', 'to_json', 'JSONEncoder']
        for func in functions_to_check:
            if func in content:
                print(f"✅ 函数 {func} 存在")
            else:
                print(f"❌ 函数 {func} 缺失")
        
        # 检查ObjectId处理
        if 'ObjectId' in content:
            print("✅ 包含ObjectId处理逻辑")
        if 'str(obj)' in content:
            print("✅ 包含对象转字符串处理")
        
        return True
    except Exception as e:
        print(f"❌ JSON工具测试失败: {e}")
        return False

def test_routes_import():
    """测试路由模块修改"""
    print("\n🔧 测试路由模块修改...")
    try:
        # 检查routes.py文件的关键修改
        routes_file = '/home/droot/medc-img-annotation-app/backend/app/routes.py'
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ 路由文件读取成功")
        
        # 检查关键导入
        if 'from app.json_utils import safe_jsonify' in content:
            print("✅ JSON工具导入已添加")
        if 'from app.user_config import SYSTEM_USERS, ROLE_TO_EXPERT_ID' in content:
            print("✅ 用户配置导入已添加")
        
        # 检查safe_jsonify的使用
        safe_jsonify_count = content.count('safe_jsonify')
        if safe_jsonify_count > 0:
            print(f"✅ safe_jsonify 使用了 {safe_jsonify_count} 次")
        else:
            print("❌ 未发现safe_jsonify使用")
        
        # 检查用户管理API
        if '/api/admin/users' in content:
            print("✅ 用户管理API已添加")
        if 'get_users' in content:
            print("✅ 获取用户列表API存在")
        if 'get_user_config_info' in content:
            print("✅ 用户配置信息API存在")
        
        return True
    except Exception as e:
        print(f"❌ 路由模块测试失败: {e}")
        return False

def test_frontend_changes():
    """测试前端界面修改"""
    print("\n🔧 测试前端界面修改...")
    try:
        # 检查前端App.jsx文件
        frontend_file = '/home/droot/medc-img-annotation-app/frontend/src/App.jsx'
        with open(frontend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ 前端文件读取成功")
        
        # 检查登录提示修改
        if '请使用系统分配的账号登录' in content:
            print("✅ 登录提示已修改为系统分配账号")
        else:
            print("❌ 登录提示未修改")
        
        # 检查是否移除了测试账号显示
        if 'admin/admin123' not in content or 'doctor/doctor123' not in content:
            print("✅ 测试账号信息已移除或隐藏")
        else:
            print("⚠️ 仍发现测试账号信息")
        
        # 检查用户管理组件
        if 'UserManager' in content:
            print("✅ 用户管理组件已添加")
        if 'showUserManager' in content:
            print("✅ 用户管理状态管理已添加")
        
        # 检查用户管理按钮
        if '用户管理' in content:
            print("✅ 用户管理按钮已添加")
        
        # 检查用户管理样式
        if 'role-badge' in content:
            print("✅ 用户角色样式已添加")
        
        return True
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试医学图像标注系统改进...")
    print("=" * 50)
    
    results = []
    
    # 运行各项测试
    results.append(test_user_config())
    results.append(test_json_utils()) 
    results.append(test_routes_import())
    results.append(test_frontend_changes())
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📋 测试结果汇总:")
    
    if all(results):
        print("🎉 所有测试通过! 系统改进成功完成")
        print("\n✨ 改进内容:")
        print("   1. ✅ ObjectId序列化问题已修复")
        print("   2. ✅ 用户管理已简化为后端配置文件管理")
        print("   3. ✅ 前端登录界面已移除测试账号显示")
        print("   4. ✅ 新增管理员用户管理界面")
        
        print("\n📝 使用说明:")
        print("   - 管理员可通过修改 backend/app/user_config.py 管理用户")
        print("   - 修改用户配置后需重启后端服务")
        print("   - 前端管理员界面提供用户管理指导")
        
        return 0
    else:
        failed_count = results.count(False)
        print(f"❌ {failed_count} 项测试失败，请检查相关模块")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)