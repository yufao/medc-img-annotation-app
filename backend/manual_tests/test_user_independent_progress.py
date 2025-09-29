#!/usr/bin/env python3
"""
手工测试：用户独立进度（需后端运行中）
"""
import requests
import time

BASE_URL = "http://localhost:5000"
TEST_DATASET_ID = 1

test_users = [
    {"username": "dtr001", "password": "fst222", "role": "doctor"},
    {"username": "stu001", "password": "std333", "role": "student"}
]

def main():
    print("🔄 开始测试用户独立进度功能...")
    for user in test_users:
        username = user["username"]
        password = user["password"]
        role = user["role"]
        # login
        r = requests.post(f"{BASE_URL}/api/login", json={"username": username, "password": password})
        if r.ok and r.json().get("msg") == "success":
            print(f"✅ 登录: {username}")
        else:
            print(f"❌ 登录失败: {username}", r.text)
            continue
        # next image
        r = requests.post(f"{BASE_URL}/api/next_image", json={"dataset_id": TEST_DATASET_ID, "expert_id": username, "role": role})
        data = r.json() if r.ok else {}
        print("next:", data)
        if "image_id" in data:
            # annotate
            a = requests.post(f"{BASE_URL}/api/annotate", json={
                "dataset_id": TEST_DATASET_ID,
                "image_id": data["image_id"],
                "expert_id": username,
                "label": 1,
                "tip": f"手工测试 - {username}"
            })
            print("annotate:", a.text)
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败！请先启动后端服务（backend/run.py）")
