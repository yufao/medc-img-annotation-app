#!/usr/bin/env python3
"""
标注系统并发压力测试
模拟多个用户同时进行标注操作，验证record_id的唯一性和并发安全性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from db_utils import get_next_annotation_id
import threading
import time
import random
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://172.20.48.1:27017/local')
MONGO_DB = os.getenv('MONGODB_DB', 'local')

def concurrent_annotation_test():
    """并发标注测试"""
    print("=== 并发标注压力测试 ===")
    
    # 测试参数
    THREAD_COUNT = 5  # 并发线程数
    ANNOTATIONS_PER_THREAD = 10  # 每个线程创建的标注数
    
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    
    # 记录测试开始前的数据库状态
    initial_count = db.annotations.count_documents({})
    print(f"测试开始前数据库中标注数: {initial_count}")
    
    # 用于收集所有生成的record_id
    all_record_ids = []
    lock = threading.Lock()
    
    # 用于记录线程执行时间
    thread_times = {}
    
    def annotate_worker(thread_id):
        """工作线程：模拟用户标注操作"""
        start_time = time.time()
        thread_record_ids = []
        
        for i in range(ANNOTATIONS_PER_THREAD):
            try:
                # 模拟标注数据
                annotation_data = {
                    'dataset_id': random.randint(1, 3),
                    'image_id': random.randint(1, 100),
                    'expert_id': thread_id,  # 使用线程ID作为专家ID
                    'label_id': random.randint(1, 5),
                    'tip': f'线程{thread_id}的第{i+1}个标注',
                    'datetime': datetime.now().isoformat()
                }
                
                # 获取唯一的record_id
                record_id = get_next_annotation_id(db)
                annotation_data['record_id'] = record_id
                
                # 保存到数据库
                result = db.annotations.insert_one(annotation_data)
                
                thread_record_ids.append(record_id)
                print(f"线程{thread_id}: 标注{i+1}, record_id={record_id}, ObjectId={result.inserted_id}")
                
                # 模拟处理时间
                time.sleep(random.uniform(0.01, 0.05))
                
            except Exception as e:
                print(f"❌ 线程{thread_id}标注{i+1}失败: {e}")
        
        end_time = time.time()
        
        # 线程安全地添加到全局列表
        with lock:
            all_record_ids.extend(thread_record_ids)
            thread_times[thread_id] = end_time - start_time
        
        print(f"✅ 线程{thread_id}完成，耗时{end_time - start_time:.2f}秒")
    
    # 创建并启动所有线程
    threads = []
    test_start_time = time.time()
    
    print(f"\n启动{THREAD_COUNT}个并发线程，每个线程创建{ANNOTATIONS_PER_THREAD}个标注...")
    
    for i in range(THREAD_COUNT):
        thread = threading.Thread(target=annotate_worker, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    test_end_time = time.time()
    
    # 分析测试结果
    print(f"\n=== 测试结果分析 ===")
    print(f"总耗时: {test_end_time - test_start_time:.2f}秒")
    print(f"平均线程耗时: {sum(thread_times.values()) / len(thread_times):.2f}秒")
    
    # 检查record_id唯一性
    total_generated = len(all_record_ids)
    unique_record_ids = set(all_record_ids)
    unique_count = len(unique_record_ids)
    
    print(f"生成的record_id总数: {total_generated}")
    print(f"唯一record_id数量: {unique_count}")
    print(f"record_id范围: {min(all_record_ids)} - {max(all_record_ids)}")
    
    if total_generated == unique_count:
        print("✅ 并发唯一性测试通过：所有record_id都是唯一的")
    else:
        print("❌ 并发唯一性测试失败：发现重复的record_id")
        duplicates = [rid for rid in all_record_ids if all_record_ids.count(rid) > 1]
        print(f"重复的record_id: {set(duplicates)}")
    
    # 验证数据库状态
    final_count = db.annotations.count_documents({})
    expected_count = initial_count + (THREAD_COUNT * ANNOTATIONS_PER_THREAD)
    
    print(f"测试后数据库中标注数: {final_count}")
    print(f"预期标注数: {expected_count}")
    
    if final_count == expected_count:
        print("✅ 数据库一致性检查通过")
    else:
        print(f"❌ 数据库一致性检查失败：缺少{expected_count - final_count}条记录")
    
    # 检查数据库中是否有重复的record_id
    pipeline = [
        {"$group": {"_id": "$record_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    db_duplicates = list(db.annotations.aggregate(pipeline))
    
    if not db_duplicates:
        print("✅ 数据库record_id唯一性检查通过")
    else:
        print(f"❌ 数据库中发现{len(db_duplicates)}个重复的record_id")
        for dup in db_duplicates:
            print(f"   record_id {dup['_id']}: {dup['count']} 条记录")
    
    client.close()
    
    if total_generated == unique_count and final_count == expected_count and not db_duplicates:
        print("\n🎉 并发压力测试完全通过！")
        return True
    else:
        print("\n❌ 并发压力测试失败！")
        return False

if __name__ == "__main__":
    success = concurrent_annotation_test()
    sys.exit(0 if success else 1)
