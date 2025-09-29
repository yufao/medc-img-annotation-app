from pymongo import MongoClient, ASCENDING
import logging

def init_database(mongo_uri, db_name):
    """初始化数据库结构，处理版本升级"""
    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        # 检查数据库版本
        system_info = db.system_info.find_one({"key": "db_version"})
        current_version = system_info.get("value", 0) if system_info else 0
        
        logging.info(f"当前数据库版本: {current_version}")
        
        # 如果版本低于1，执行v1升级
        if current_version < 1:
            upgrade_to_v1(db)
            # 更新数据库版本
            db.system_info.update_one(
                {"key": "db_version"}, 
                {"$set": {"value": 1}}, 
                upsert=True
            )
            logging.info("数据库已升级到版本1")
            current_version = 1

        # 如果版本低于2，执行v2升级（添加热点索引）
        if current_version < 2:
            upgraded = upgrade_to_v2(db)
            if upgraded:
                db.system_info.update_one(
                    {"key": "db_version"},
                    {"$set": {"value": 2}},
                    upsert=True
                )
                logging.info("数据库已升级到版本2（索引创建）")
            else:
                logging.warning("数据库升级到版本2失败，后续可重试或手动创建索引")
        
        return True
    except Exception as e:
        logging.error(f"数据库初始化失败: {str(e)}")
        return False

def upgrade_to_v1(db):
    """升级数据库到版本1（添加数据集特定标签支持）"""
    try:
        # 1. 为标签添加dataset_id字段
        # 查找所有没有dataset_id的标签
        labels_without_dataset = list(db.labels.find({"dataset_id": {"$exists": False}}))
        
        # 将它们标记为通用标签（dataset_id为null）
        for label in labels_without_dataset:
            db.labels.update_one(
                {"_id": label["_id"]},
                {"$set": {"dataset_id": None}}
            )
        
        logging.info(f"已将{len(labels_without_dataset)}个标签更新为通用标签")
        
        # 2. 确保每个数据集有正确的图片计数
        datasets = list(db.datasets.find({}))
        for dataset in datasets:
            dataset_id = dataset.get("id")
            if dataset_id is not None:
                # 计算实际图片数量
                actual_count = db.image_datasets.count_documents({"dataset_id": dataset_id})
                
                # 更新数据集记录
                db.datasets.update_one(
                    {"id": dataset_id},
                    {"$set": {"image_count": actual_count}}
                )
                
                logging.info(f"数据集 {dataset_id} 图片数量已校正: {actual_count} 张")
                
        return True
    except Exception as e:
        logging.error(f"升级到版本1失败: {str(e)}")
        return False


def upgrade_to_v2(db):
    """升级数据库到版本2（添加常用复合索引与单键索引）。

    - annotations: (dataset_id, expert_id, image_id)
    - image_datasets: (dataset_id, image_id)
    - labels: (dataset_id, label_id)
    - images: (image_id)
    """
    try:
        # annotations 复合索引
        try:
            db.annotations.create_index([
                ("dataset_id", ASCENDING), ("expert_id", ASCENDING), ("image_id", ASCENDING)
            ], name="ann_ds_expert_img")
        except Exception as e:
            logging.debug(f"annotations 索引创建提示: {e}")

        # image_datasets 复合索引
        try:
            db.image_datasets.create_index([
                ("dataset_id", ASCENDING), ("image_id", ASCENDING)
            ], name="imgds_ds_img")
        except Exception as e:
            logging.debug(f"image_datasets 索引创建提示: {e}")

        # labels 复合索引
        try:
            db.labels.create_index([
                ("dataset_id", ASCENDING), ("label_id", ASCENDING)
            ], name="labels_ds_label")
        except Exception as e:
            logging.debug(f"labels 索引创建提示: {e}")

        # images 单键索引
        try:
            db.images.create_index([("image_id", ASCENDING)], name="images_image_id")
        except Exception as e:
            logging.debug(f"images 索引创建提示: {e}")

        return True
    except Exception as e:
        logging.error(f"升级到版本2失败: {str(e)}")
        return False
