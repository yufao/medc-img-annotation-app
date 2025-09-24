#!/usr/bin/env python3
"""
测试用户独立进度功能
验证每个用户账号有独立的标注进度
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_DATASET_ID = 1

# 测试用户
test_users = [
    {"username": "dtr001", "password": "fst222", "role": "doctor"},
    {"username": "stu001", "password": "std333", "role": "student"}
]

def test_login(username, password):
    """测试登录"""
    url = f"{BASE_URL}/api/login"
    data = {"username": username, "password": password}
    response = requests.post(url, json=data)
    return response.json()

def test_next_image(username, role):
    """测试获取下一张图片"""
    url = f"{BASE_URL}/api/next_image"
    data = {
        "dataset_id": TEST_DATASET_ID,
        "expert_id": username,
        "role": role
    }
    response = requests.post(url, json=data)
    return response.json()

def test_annotate(username, role, image_id, label):
    """测试提交标注"""
    url = f"{BASE_URL}/api/annotate"
    data = {
        "dataset_id": TEST_DATASET_ID,
        "image_id": image_id,
        "expert_id": username,
        "label": label,
        "tip": f"测试标注 - 用户 {username}"
    }
    response = requests.post(url, json=data)
    return response.json()

def main():
    print("🔄 开始测试用户独立进度功能...")
    
    # 测试每个用户
    for user in test_users:
        username = user["username"]
        password = user["password"]
        role = user["role"]
        
        print(f"\n👤 测试用户: {username} ({role})")
        
        # 1. 测试登录
        login_result = test_login(username, password)
        if login_result.get("msg") != "success":
            print(f"❌ 用户 {username} 登录失败: {login_result}")
            continue
        print(f"✅ 用户 {username} 登录成功")
        
        # 2. 获取下一张图片
        next_img_result = test_next_image(username, role)
        if "image_id" in next_img_result:
            image_id = next_img_result["image_id"]
            filename = next_img_result["filename"]
            print(f"📷 用户 {username} 获取图片: {filename} (ID: {image_id})")
            
            # 3. 提交标注
            annotate_result = test_annotate(username, role, image_id, 1)  # 假设标签ID为1
            if annotate_result.get("msg") == "saved":
                print(f"✅ 用户 {username} 标注成功")
            else:
                print(f"❌ 用户 {username} 标注失败: {annotate_result}")
        elif next_img_result.get("msg") == "done":
            print(f"🎯 用户 {username} 已完成所有图片标注")
        else:
            print(f"❌ 用户 {username} 获取图片失败: {next_img_result}")
        
        time.sleep(1)  # 避免请求过快
    
    print("\n📊 验证用户进度独立性...")
    
    # 重新检查每个用户的下一张图片
    for user in test_users:
        username = user["username"]
        role = user["role"]
        
        next_img_result = test_next_image(username, role)
        if "image_id" in next_img_result:
            print(f"📷 用户 {username} 的下一张图片: {next_img_result['filename']} (ID: {next_img_result['image_id']})")
        elif next_img_result.get("msg") == "done":
            print(f"🎯 用户 {username} 已完成所有标注")
        else:
            print(f"❓ 用户 {username} 状态: {next_img_result}")
    
    print("\n✅ 用户独立进度测试完成！")
    print("💡 如果每个用户看到不同的图片或进度，说明独立进度功能正常工作。")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败！请先启动后端服务：")
        print("   cd /home/droot/medc-img-annotation-app/backend")
        print("   python run.py")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")