#!/usr/bin/env python3
"""
重构后的MongoDB数据库结构初始化脚本
按照新的数据结构要求：
- annotations: dataset_id | record_id | image_id | expert_id | label_id | tip | datetime
- images: image_id | image_path
- labels: label_id | label_name | category
"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://172.20.48.1:27017/local')
MONGO_DB = os.getenv('MONGODB_DB', 'local')

def setup_database():
    """初始化重构后的数据库结构和测试数据"""
    
    try:
        # 连接MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # 测试连接
        db = client[MONGO_DB]
        
        print(f"✅ 连接到MongoDB: {MONGO_URI}")
        print(f"✅ 使用数据库: {MONGO_DB}")
        
        # 清理现有数据
        print("\n🧹 清理现有数据...")
        db.datasets.delete_many({})
        db.images.delete_many({})
        db.labels.delete_many({})
        db.annotations.delete_many({})
        
        # 1. 创建数据集 (保持原有结构，用于管理)
        print("\n📊 创建数据集...")
        datasets = [
            {
                "id": 1,
                "name": "胸片病毒检测数据集", 
                "description": "用于检测胸片中的病毒感染",
                "created_at": "2025-07-21T00:00:00Z",
                "image_count": 10,
                "status": "active"
            },
            {
                "id": 2,
                "name": "细菌感染检测数据集", 
                "description": "用于检测CT影像中的细菌感染",
                "created_at": "2025-07-21T00:00:00Z",
                "image_count": 10,
                "status": "active"
            }
        ]
        
        result = db.datasets.insert_many(datasets)
        print(f"   ✅ 插入了 {len(result.inserted_ids)} 个数据集")
        
        # 2. 创建标签表 - 新结构: label_id | label_name | category
        print("\n🏷️ 创建标签表...")
        labels = [
            # 基础诊断标签
            {"label_id": 1, "label_name": "正常", "category": "病理学"},
            {"label_id": 2, "label_name": "病毒感染", "category": "病理学"},
            {"label_id": 3, "label_name": "细菌感染", "category": "病理学"},
            {"label_id": 4, "label_name": "疑似感染", "category": "病理学"},
            {"label_id": 5, "label_name": "肺炎", "category": "病理学"},
            {"label_id": 6, "label_name": "结节", "category": "解剖学"},
            {"label_id": 7, "label_name": "积液", "category": "解剖学"},
            {"label_id": 8, "label_name": "气胸", "category": "解剖学"},
        ]
        
        result = db.labels.insert_many(labels)
        print(f"   ✅ 插入了 {len(result.inserted_ids)} 个标签")
        
        # 3. 创建图片表 - 新结构: image_id | image_path
        print("\n🖼️ 创建图片表...")
        images = [
            # 数据集1 - 胸片病毒检测
            {"image_id": 1, "image_path": "static/img/person1_virus_6.jpeg"},
            {"image_id": 2, "image_path": "static/img/person1_virus_7.jpeg"},
            {"image_id": 3, "image_path": "static/img/person1_virus_8.jpeg"},
            {"image_id": 4, "image_path": "static/img/person1_virus_9.jpeg"},
            {"image_id": 5, "image_path": "static/img/person3_virus_15.jpeg"},
            {"image_id": 6, "image_path": "static/img/person3_virus_16.jpeg"},
            {"image_id": 7, "image_path": "static/img/person3_virus_17.jpeg"},
            {"image_id": 8, "image_path": "static/img/person8_virus_27.jpeg"},
            {"image_id": 9, "image_path": "static/img/person8_virus_28.jpeg"},
            {"image_id": 10, "image_path": "static/img/person10_virus_35.jpeg"},
            
            # 数据集2 - 细菌感染检测
            {"image_id": 11, "image_path": "static/img/person78_bacteria_378.jpeg"},
            {"image_id": 12, "image_path": "static/img/person78_bacteria_380.jpeg"},
            {"image_id": 13, "image_path": "static/img/person78_bacteria_381.jpeg"},
            {"image_id": 14, "image_path": "static/img/person78_bacteria_382.jpeg"},
            {"image_id": 15, "image_path": "static/img/person80_bacteria_389.jpeg"},
            {"image_id": 16, "image_path": "static/img/person80_bacteria_390.jpeg"},
            {"image_id": 17, "image_path": "static/img/person80_bacteria_391.jpeg"},
            {"image_id": 18, "image_path": "static/img/person80_bacteria_392.jpeg"},
            {"image_id": 19, "image_path": "static/img/person80_bacteria_393.jpeg"},
            {"image_id": 20, "image_path": "static/img/person78_bacteria_384.jpeg"},
        ]
        
        result = db.images.insert_many(images)
        print(f"   ✅ 插入了 {len(result.inserted_ids)} 个图片记录")
        
        # 4. 创建图片与数据集的关联表（辅助表）
        print("\n🔗 创建图片-数据集关联...")
        image_datasets = [
            # 数据集1的图片
            {"image_id": 1, "dataset_id": 1},
            {"image_id": 2, "dataset_id": 1},
            {"image_id": 3, "dataset_id": 1},
            {"image_id": 4, "dataset_id": 1},
            {"image_id": 5, "dataset_id": 1},
            {"image_id": 6, "dataset_id": 1},
            {"image_id": 7, "dataset_id": 1},
            {"image_id": 8, "dataset_id": 1},
            {"image_id": 9, "dataset_id": 1},
            {"image_id": 10, "dataset_id": 1},
            
            # 数据集2的图片
            {"image_id": 11, "dataset_id": 2},
            {"image_id": 12, "dataset_id": 2},
            {"image_id": 13, "dataset_id": 2},
            {"image_id": 14, "dataset_id": 2},
            {"image_id": 15, "dataset_id": 2},
            {"image_id": 16, "dataset_id": 2},
            {"image_id": 17, "dataset_id": 2},
            {"image_id": 18, "dataset_id": 2},
            {"image_id": 19, "dataset_id": 2},
            {"image_id": 20, "dataset_id": 2},
        ]
        
        result = db.image_datasets.insert_many(image_datasets)
        print(f"   ✅ 插入了 {len(result.inserted_ids)} 个图片-数据集关联记录")
        
        # 5. 创建示例标注 - 新结构: dataset_id | record_id | image_id | expert_id | label_id | tip | datetime
        print("\n📝 创建示例标注...")
        sample_annotations = [
            {
                "dataset_id": 1,
                "record_id": 1,
                "image_id": 1,
                "expert_id": 1,  # doctor
                "label_id": 2,   # 病毒感染
                "tip": "明显的病毒感染迹象",
                "datetime": "2025-07-21T10:00:00Z"
            },
            {
                "dataset_id": 1,
                "record_id": 2,
                "image_id": 2,
                "expert_id": 2,  # student
                "label_id": 1,   # 正常
                "tip": "看起来正常",
                "datetime": "2025-07-21T10:30:00Z"
            },
            {
                "dataset_id": 2,
                "record_id": 3,
                "image_id": 11,
                "expert_id": 1,  # doctor
                "label_id": 3,   # 细菌感染
                "tip": "疑似细菌感染",
                "datetime": "2025-07-21T11:00:00Z"
            },
            {
                "dataset_id": 2,
                "record_id": 4,
                "image_id": 12,
                "expert_id": 0,  # admin (真实标签)
                "label_id": 5,   # 肺炎
                "tip": "确诊肺炎",
                "datetime": "2025-07-21T11:30:00Z"
            },
        ]
        
        result = db.annotations.insert_many(sample_annotations)
        print(f"   ✅ 插入了 {len(result.inserted_ids)} 个示例标注")
        
        # 6. 创建索引提高性能
        print("\n⚡ 创建数据库索引...")
        db.images.create_index("image_id", unique=True)
        db.labels.create_index("label_id", unique=True)
        db.annotations.create_index([("dataset_id", 1), ("image_id", 1), ("expert_id", 1)])
        db.annotations.create_index("record_id", unique=True)
        db.image_datasets.create_index([("image_id", 1), ("dataset_id", 1)])
        print("   ✅ 索引创建完成")
        
        # 7. 验证数据
        print("\n✅ 数据验证:")
        print(f"   📊 数据集: {db.datasets.count_documents({})}")
        print(f"   🖼️ 图片: {db.images.count_documents({})}")
        print(f"   🏷️ 标签: {db.labels.count_documents({})}")
        print(f"   📝 标注: {db.annotations.count_documents({})}")
        print(f"   🔗 图片-数据集关联: {db.image_datasets.count_documents({})}")
        
        # 8. 显示数据结构示例
        print("\n📋 数据结构预览:")
        
        print("\n   标注表结构:")
        print("   dataset_id | record_id | image_id | expert_id | label_id | tip | datetime")
        sample_annotation = db.annotations.find_one()
        if sample_annotation:
            print(f"   {sample_annotation.get('dataset_id', 'N/A')} | {sample_annotation.get('record_id', 'N/A')} | {sample_annotation.get('image_id', 'N/A')} | {sample_annotation.get('expert_id', 'N/A')} | {sample_annotation.get('label_id', 'N/A')} | {sample_annotation.get('tip', 'N/A')[:10]}... | {sample_annotation.get('datetime', 'N/A')[:19]}")
        
        print("\n   图片表结构:")
        print("   image_id | image_path")
        sample_image = db.images.find_one()
        if sample_image:
            print(f"   {sample_image.get('image_id', 'N/A')} | {sample_image.get('image_path', 'N/A')}")
        
        print("\n   标签表结构:")
        print("   label_id | label_name | category")
        sample_label = db.labels.find_one()
        if sample_label:
            print(f"   {sample_label.get('label_id', 'N/A')} | {sample_label.get('label_name', 'N/A')} | {sample_label.get('category', 'N/A')}")
        
        print(f"\n🎉 重构后的数据库初始化完成！")
        print(f"💡 新的数据结构已经就绪，可以进行Excel多工作表导出")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def show_current_data():
    """显示当前数据库的数据"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[MONGO_DB]
        
        print("📋 当前数据库内容:")
        print(f"📊 数据集: {db.datasets.count_documents({})}")
        print(f"🖼️ 图片: {db.images.count_documents({})}")
        print(f"🏷️ 标签: {db.labels.count_documents({})}")
        print(f"📝 标注: {db.annotations.count_documents({})}")
        
        # 显示标注数据的字段结构
        annotations = list(db.annotations.find({}).limit(3))
        if annotations:
            print("\n标注数据结构示例:")
            for i, ann in enumerate(annotations, 1):
                ann.pop('_id', None)  # 移除MongoDB内部ID
                print(f"  记录{i}: {ann}")
        
    except Exception as e:
        print(f"❌ 查看数据失败: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_current_data()
    else:
        setup_database()
