#!/usr/bin/env python3
"""
测试标注保存功能（手工测试）
验证自增序列ID生成和数据库保存的正确性
"""

import sys
import os
# 将 backend 目录加入 sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from pymongo import MongoClient
from db_utils import get_next_annotation_id
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.getenv('MONGODB_DB', 'local')

def main():
    """测试标注保存功能"""
    print("=== 测试标注保存功能 ===")
    
    # 连接数据库
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    
    # 测试数据
    test_annotation = {
        'dataset_id': 1,
        'image_id': 15,
        'expert_id': 3,
        'label_id': 2,
        'tip': '测试标注 - 数据库修复后的标注'
    }
    
    print(f"1. 测试标注数据: {test_annotation}")
    
    # 使用自增序列获取下一个record_id
    next_record_id = get_next_annotation_id(db)
    print(f"2. 使用自增序列分配的record_id: {next_record_id}")
    
    # 添加record_id和时间戳
    test_annotation['record_id'] = next_record_id
    test_annotation['datetime'] = '2025-07-23T18:30:00Z'
    
    try:
        # 保存标注
        result = db.annotations.insert_one(test_annotation)
        print(f"3. ✅ 标注保存成功，ObjectId: {result.inserted_id}")
        
        # 验证保存结果
        saved_annotation = db.annotations.find_one({'record_id': next_record_id})
        print(f"4. 验证保存的标注: {saved_annotation}")
        
        # 检查是否有重复的record_id
        duplicate_count = db.annotations.count_documents({'record_id': next_record_id})
        print(f"5. record_id {next_record_id} 的记录数量: {duplicate_count}")
        
        if duplicate_count == 1:
            print("✅ record_id唯一性检查通过")
        else:
            print(f"❌ 警告：发现重复的record_id {next_record_id}")
        
        # 检查总记录数
        total_count = db.annotations.count_documents({})
        print(f"6. 数据库中总标注数: {total_count}")
        
        print("🎉 标注保存测试完成！")
        
    except Exception as e:
        print(f"❌ 标注保存失败: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    main()
