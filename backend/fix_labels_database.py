#!/usr/bin/env python3
"""
数据库标签修复脚本
用于修复没有dataset_id的历史标签数据

使用方法：
1. 确保MongoDB服务运行
2. 运行: python fix_labels_database.py
"""

import sys
import os
from pymongo import MongoClient
from datetime import datetime

# 添加配置文件路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import MONGO_URI, MONGO_DB

def connect_database():
    """连接数据库"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # 测试连接
        db = client[MONGO_DB]
        print(f"✅ 数据库连接成功: {MONGO_URI}")
        print(f"✅ 使用数据库: {MONGO_DB}")
        return db
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def analyze_labels_data(db):
    """分析当前标签数据的状况"""
    print("\n🔍 分析当前标签数据...")
    
    # 统计所有标签
    total_labels = db.labels.count_documents({})
    print(f"总标签数量: {total_labels}")
    
    # 统计有dataset_id的标签
    labels_with_dataset = db.labels.count_documents({"dataset_id": {"$exists": True}})
    print(f"已关联数据集的标签: {labels_with_dataset}")
    
    # 统计没有dataset_id的标签
    labels_without_dataset = db.labels.count_documents({"dataset_id": {"$exists": False}})
    print(f"未关联数据集的标签: {labels_without_dataset}")
    
    # 获取所有数据集
    datasets = list(db.datasets.find({}, {"_id": 0, "id": 1, "name": 1}))
    print(f"\n📋 现有数据集:")
    for ds in datasets:
        print(f"  - ID: {ds['id']}, 名称: {ds['name']}")
    
    # 显示没有dataset_id的标签
    if labels_without_dataset > 0:
        print(f"\n🏷️ 未关联数据集的标签:")
        orphan_labels = list(db.labels.find({"dataset_id": {"$exists": False}}, {"_id": 0}))
        for label in orphan_labels:
            print(f"  - ID: {label.get('label_id')}, 名称: {label.get('label_name')}")
    
    return datasets, orphan_labels if labels_without_dataset > 0 else []

def interactive_assign_labels(db, datasets, orphan_labels):
    """交互式分配标签到数据集"""
    if not orphan_labels:
        print("✅ 没有需要分配的孤立标签")
        return
    
    print(f"\n📝 开始分配 {len(orphan_labels)} 个孤立标签...")
    
    for label in orphan_labels:
        label_id = label.get('label_id')
        label_name = label.get('label_name')
        
        print(f"\n🏷️ 处理标签: ID={label_id}, 名称={label_name}")
        print("请选择要分配给哪个数据集:")
        print("0. 保持为通用标签（不分配给特定数据集）")
        
        for i, ds in enumerate(datasets, 1):
            print(f"{i}. {ds['name']} (ID: {ds['id']})")
        
        while True:
            try:
                choice = input("请输入选择 (0-{max_choice}): ".format(max_choice=len(datasets)))
                choice = int(choice)
                
                if choice == 0:
                    print(f"标签 {label_name} 保持为通用标签")
                    break
                elif 1 <= choice <= len(datasets):
                    selected_dataset = datasets[choice - 1]
                    # 更新标签，添加dataset_id
                    result = db.labels.update_one(
                        {"label_id": label_id},
                        {"$set": {"dataset_id": selected_dataset['id']}}
                    )
                    if result.modified_count > 0:
                        print(f"✅ 标签 {label_name} 已分配给数据集 {selected_dataset['name']}")
                    else:
                        print(f"❌ 分配失败")
                    break
                else:
                    print(f"无效选择，请输入 0-{len(datasets)} 之间的数字")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n⚠️ 操作被取消")
                return

def batch_assign_by_pattern(db, datasets, orphan_labels):
    """基于模式批量分配标签"""
    if not orphan_labels:
        return
    
    print(f"\n🚀 批量分配选项:")
    print("1. 将所有孤立标签分配给第一个数据集")
    print("2. 将所有孤立标签保持为通用标签")
    print("3. 返回交互式分配")
    
    choice = input("请选择 (1-3): ")
    
    if choice == "1" and datasets:
        first_dataset = datasets[0]
        print(f"将所有孤立标签分配给数据集: {first_dataset['name']}")
        confirm = input("确认吗？(y/N): ")
        if confirm.lower() == 'y':
            result = db.labels.update_many(
                {"dataset_id": {"$exists": False}},
                {"$set": {"dataset_id": first_dataset['id']}}
            )
            print(f"✅ 已将 {result.modified_count} 个标签分配给数据集 {first_dataset['name']}")
    elif choice == "2":
        print("保持所有标签为通用标签，无需操作")
    elif choice == "3":
        interactive_assign_labels(db, datasets, orphan_labels)

def main():
    print("🔧 医学图像标注系统 - 标签数据库修复工具")
    print("=" * 50)
    
    # 连接数据库
    db = connect_database()
    if db is None:
        return
    
    # 分析现有数据
    datasets, orphan_labels = analyze_labels_data(db)
    
    if not orphan_labels:
        print("\n✅ 所有标签都已正确关联到数据集，无需修复")
        return
    
    print(f"\n⚠️ 发现 {len(orphan_labels)} 个未关联数据集的标签需要处理")
    
    # 选择处理方式
    print("\n处理方式:")
    print("1. 交互式分配（逐个选择）")
    print("2. 批量分配")
    print("3. 退出")
    
    choice = input("请选择 (1-3): ")
    
    if choice == "1":
        interactive_assign_labels(db, datasets, orphan_labels)
    elif choice == "2":
        batch_assign_by_pattern(db, datasets, orphan_labels)
    elif choice == "3":
        print("退出修复工具")
        return
    else:
        print("无效选择")
        return
    
    # 再次分析数据，显示修复结果
    print("\n" + "=" * 50)
    print("🎉 修复完成，最终状态:")
    analyze_labels_data(db)

if __name__ == "__main__":
    main()