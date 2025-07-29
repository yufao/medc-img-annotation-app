#!/usr/bin/env python3
"""
MongoDB数据库工具脚本
- 数据库清理功能
- 自增序列管理
- 序列状态检查
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import time
import random
import threading
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://172.20.48.1:27017/local')
MONGO_DB = os.getenv('MONGODB_DB', 'local')

class SequenceGenerator:
    """MongoDB自增序列生成器"""
    
    def __init__(self, db):
        self.db = db
    
    def get_next_sequence_value(self, sequence_name, initial_value=0):
        """
        获取下一个序列值（原子操作，并发安全）
        
        Args:
            sequence_name: 序列名称
            initial_value: 初始值（当序列不存在时使用）
        
        Returns:
            int: 下一个序列值
        """
        try:
            # 使用findOneAndUpdate进行原子操作
            result = self.db.sequences.find_one_and_update(
                {"_id": sequence_name},
                {"$inc": {"sequence_value": 1}},
                return_document=True,  # 返回更新后的文档
                upsert=True  # 如果不存在则创建
            )
            
            # 如果是新创建的序列，需要设置初始值
            if result["sequence_value"] == 1 and initial_value > 0:
                # 更新为指定的初始值
                result = self.db.sequences.find_one_and_update(
                    {"_id": sequence_name},
                    {"$set": {"sequence_value": initial_value + 1}},
                    return_document=True
                )
                return initial_value + 1
            
            return result["sequence_value"]
            
        except Exception as e:
            # 如果失败，使用备用方案（时间戳+随机数）
            print(f"序列生成失败，使用备用方案: {e}")
            return self._generate_fallback_id()
    
    def _generate_fallback_id(self):
        """备用ID生成方案（时间戳+随机数）"""
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        random_suffix = random.randint(100, 999)
        return int(f"{timestamp}{random_suffix}")
    
    def reset_sequence(self, sequence_name, value=0):
        """重置序列值"""
        self.db.sequences.update_one(
            {"_id": sequence_name},
            {"$set": {"sequence_value": value}},
            upsert=True
        )
    
    def get_current_sequence_value(self, sequence_name):
        """获取当前序列值（不递增）"""
        result = self.db.sequences.find_one({"_id": sequence_name})
        return result["sequence_value"] if result else 0

def get_next_annotation_id(db):
    """
    获取下一个标注ID的便捷函数
    
    Args:
        db: MongoDB数据库连接
    
    Returns:
        int: 下一个唯一的标注ID
    """
    generator = SequenceGenerator(db)
    
    # 获取当前数据库中最大的record_id作为初始值
    max_record = db.annotations.find_one({}, sort=[("record_id", -1)])
    initial_value = max_record.get("record_id", 0) if max_record else 0
    
    return generator.get_next_sequence_value("annotations_record_id", initial_value)

def cleanup_database():
    """清理数据库中的重复记录并设置自增序列"""
    print("=== 数据库清理和自增序列设置 ===")
    
    # 连接数据库
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    
    try:
        # 1. 检查当前数据库状态
        print("\n1. 检查当前数据库状态...")
        total_annotations = db.annotations.count_documents({})
        print(f"   当前标注总数: {total_annotations}")
        
        # 检查重复的record_id
        pipeline = [
            {"$group": {"_id": "$record_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"_id": 1}}
        ]
        duplicates = list(db.annotations.aggregate(pipeline))
        print(f"   发现重复record_id: {len(duplicates)} 个")
        for dup in duplicates:
            print(f"     record_id {dup['_id']}: {dup['count']} 条记录")
        
        # 2. 清理重复数据
        print("\n2. 清理重复数据...")
        if duplicates:
            for dup in duplicates:
                record_id = dup['_id']
                # 保留第一条记录，删除其余重复记录
                duplicate_docs = list(db.annotations.find({"record_id": record_id}).sort("_id", 1))
                if len(duplicate_docs) > 1:
                    # 保留第一条，删除其余
                    keep_doc = duplicate_docs[0]
                    delete_ids = [doc['_id'] for doc in duplicate_docs[1:]]
                    result = db.annotations.delete_many({"_id": {"$in": delete_ids}})
                    print(f"     record_id {record_id}: 保留1条，删除{result.deleted_count}条")
        
        # 3. 创建序列集合
        print("\n3. 创建自增序列集合...")
        
        # 获取当前最大的record_id
        max_record = db.annotations.find_one({}, sort=[("record_id", -1)])
        current_max = max_record.get("record_id", 0) if max_record else 0
        
        # 创建序列文档
        sequence_doc = {
            "_id": "annotations_record_id",
            "sequence_value": current_max
        }
        db.sequences.update_one(
            {"_id": "annotations_record_id"},
            {"$set": {"sequence_value": current_max}},
            upsert=True
        )
        print(f"   创建或更新序列集合，当前值: {current_max}")
        
        # 4. 验证清理结果
        print("\n4. 验证清理结果...")
        total_after = db.annotations.count_documents({})
        duplicates_after = list(db.annotations.aggregate(pipeline))
        
        print(f"   清理后标注总数: {total_after}")
        print(f"   清理后重复记录: {len(duplicates_after)} 个")
        
        if len(duplicates_after) == 0:
            print("   ✅ 重复数据清理成功")
        else:
            print("   ❌ 仍存在重复数据")
            for dup in duplicates_after:
                print(f"     record_id {dup['_id']}: {dup['count']} 条记录")
        
        # 5. 创建索引确保唯一性
        print("\n5. 创建唯一索引...")
        try:
            db.annotations.create_index([("record_id", 1)], unique=True)
            print("   ✅ 创建record_id唯一索引成功")
        except Exception as e:
            print(f"   ⚠️  索引可能已存在: {e}")
        
        print("\n🎉 数据库清理和自增序列设置完成！")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

def check_sequence_status():
    """检查序列状态"""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    
    try:
        # 获取序列状态
        sequence = db.sequences.find_one({"_id": "annotations_record_id"})
        if sequence:
            print(f"序列 'annotations_record_id' 当前值: {sequence['sequence_value']}")
        else:
            print("序列 'annotations_record_id' 不存在")
        
        # 获取当前最大record_id
        max_record = db.annotations.find_one({}, sort=[("record_id", -1)])
        if max_record and 'record_id' in max_record:
            print(f"数据库中最大 record_id: {max_record['record_id']}")
        else:
            print("数据库中没有标注数据")
        
        # 验证索引
        indexes = db.annotations.list_indexes()
        has_unique_index = False
        for idx in indexes:
            if 'record_id' in idx['key'] and idx.get('unique', False):
                has_unique_index = True
                print("✅ record_id唯一索引存在")
                break
        
        if not has_unique_index:
            print("⚠️ record_id唯一索引不存在")
    
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    
    finally:
        client.close()

def run_concurrent_test(thread_count=3, annotations_per_thread=5):
    """运行并发测试"""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    
    all_record_ids = []
    lock = threading.Lock()
    
    def generate_ids(thread_id):
        """线程函数：生成指定数量的ID"""
        thread_ids = []
        for i in range(annotations_per_thread):
            next_id = get_next_annotation_id(db)
            thread_ids.append(next_id)
            print(f"线程{thread_id}: 生成ID {next_id}")
            time.sleep(0.01)
        
        with lock:
            all_record_ids.extend(thread_ids)
    
    # 创建多个线程同时生成ID
    threads = []
    for i in range(thread_count):
        thread = threading.Thread(target=generate_ids, args=(i+1,))
        threads.append(thread)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 检查ID唯一性
    unique_ids = set(all_record_ids)
    
    print(f"\n生成的ID总数: {len(all_record_ids)}")
    print(f"唯一ID数量: {len(unique_ids)}")
    
    if len(all_record_ids) == len(unique_ids):
        print("✅ 并发测试成功，所有ID都是唯一的")
        return True
    else:
        print("❌ 并发测试失败，发现重复ID")
        return False
    
    client.close()

def print_help():
    """打印帮助信息"""
    print("""
MongoDB数据库工具 - 使用方法：

python db_utils.py [命令]

可用命令:
  cleanup     - 清理数据库中的重复记录并设置自增序列
  status      - 检查序列状态
  test        - 运行并发测试
  help        - 显示帮助信息
    """)

if __name__ == "__main__":
    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "cleanup":
            cleanup_database()
        elif command == "status":
            check_sequence_status()
        elif command == "test":
            run_concurrent_test()
        elif command == "help":
            print_help()
        else:
            print(f"未知命令: {command}")
            print_help()
    else:
        # 默认执行清理
        cleanup_database()
