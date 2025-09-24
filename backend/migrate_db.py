#!/usr/bin/env python3
"""Mongo 数据库迁移/克隆脚本

用途：
 1. 旧库（例如 local）迁移到新命名库（例如 medical_annotation 或 medc_annotation_prod）
 2. 初始化新库：当新库不存在或为空时复制旧库数据
 3. Dry-run 模式先看计划

特性：
 - 只复制白名单集合（默认：datasets, images, image_datasets, labels, annotations, sequences, system_info）
 - 目标集合已有数据则跳过（除非指定 --force 单集合覆盖）
 - 保留原 _id；若目标已有相同 _id 将自动跳过避免冲突
 - 提供简单统计输出

使用示例：
  python migrate_db.py --src-db local --dst-db medical_annotation
  python migrate_db.py --src-db local --dst-db medc_annotation_prod --dry-run

参数：
  --src-uri  源 Mongo URI（默认读取 MONGO_URI/MONGODB_URI 或 mongodb://localhost:27017/）
  --dst-uri  目标 Mongo URI（默认同源）
  --src-db   源数据库名 (默认: local)
  --dst-db   目标数据库名 (默认: medical_annotation)
  --collections c1,c2 覆盖默认集合白名单
  --force    若指定：在复制前清空目标集合（危险）
  --dry-run  仅读取与计划，不执行写入

安全注意：
 - 不会删除源数据
 - 使用 --force 会对目标集合执行 delete_many({})
"""
from __future__ import annotations
import os, argparse, sys
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

# 加载 .env 以支持 MONGO_URI/MONGODB_URI 等（之前缺失导致默认回退 localhost）
load_dotenv()

DEFAULT_COLLECTIONS = [
    "datasets", "images", "image_datasets", "labels", "annotations", "sequences", "system_info"
]

def parse_args():
    p = argparse.ArgumentParser(description="MongoDB 数据库迁移工具")
    env_uri = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI') or 'mongodb://localhost:27017/'
    p.add_argument('--src-uri', default=env_uri, help='源 Mongo URI')
    p.add_argument('--dst-uri', default=None, help='目标 Mongo URI (默认同源)')
    p.add_argument('--src-db', default='local', help='源数据库名')
    p.add_argument('--dst-db', default=os.getenv('MONGO_DB') or os.getenv('MONGODB_DB') or 'medical_annotation', help='目标数据库名')
    p.add_argument('--collections', default=','.join(DEFAULT_COLLECTIONS), help='逗号分隔集合列表')
    p.add_argument('--force', action='store_true', help='复制前清空目标同名集合 (危险)')
    p.add_argument('--dry-run', action='store_true', help='仅打印计划不执行')
    p.add_argument('--timeout', type=int, default=4000, help='连接超时 (ms) 默认 4000')
    p.add_argument('--ping', action='store_true', help='仅测试源与目标可达性并退出')
    p.add_argument('--list-dbs', action='store_true', help='列出源与目标实例的数据库列表并退出')
    return p.parse_args()

def connect(uri: str, timeout_ms: int):
    client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
    client.server_info()  # 触发连接
    return client

def migrate(args):
    dst_uri = args.dst_uri or args.src_uri
    cols = [c.strip() for c in args.collections.split(',') if c.strip()]
    print(f"源: {args.src_uri} / {args.src_db}\n目标: {dst_uri} / {args.dst_db}\n集合: {cols}\nDryRun: {args.dry_run}\nForce: {args.force}")
    try:
        src_client = connect(args.src_uri, args.timeout)
        dst_client = connect(dst_uri, args.timeout)
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return 1

    # 诊断模式：ping
    if args.ping:
        try:
            print("源 ping: OK")
            print("目标 ping: OK")
        finally:
            if args.list_dbs is False:
                return 0

    # 诊断模式：列出数据库
    if args.list_dbs:
        print("源实例数据库: ")
        try:
            for name in src_client.list_database_names():
                print(f"  - {name}")
        except Exception as e:
            print(f"  列出失败: {e}")
        print("目标实例数据库: ")
        try:
            for name in dst_client.list_database_names():
                print(f"  - {name}")
        except Exception as e:
            print(f"  列出失败: {e}")
        return 0
    src_db = src_client[args.src_db]
    dst_db = dst_client[args.dst_db]

    total_copied = 0
    for col in cols:
        src_col = src_db[col]
        dst_col = dst_db[col]
        src_count = src_col.count_documents({})
        dst_count = dst_col.count_documents({})
        if src_count == 0:
            print(f"- {col}: 源集合为空，跳过")
            continue
        if dst_count > 0 and not args.force:
            print(f"- {col}: 目标已有 {dst_count} 条，跳过 (使用 --force 覆盖)")
            continue
        print(f"- {col}: 计划复制 {src_count} 条 -> 目标当前 {dst_count}")
        if args.dry_run:
            continue
        if args.force and dst_count > 0:
            dst_col.delete_many({})
            print(f"  已清空目标 {col}")
        batch = []
        copied = 0
        for doc in src_col.find({}):
            batch.append(doc)
            if len(batch) >= 500:
                try:
                    dst_col.insert_many(batch, ordered=False)
                    copied += len(batch)
                except PyMongoError as e:
                    print(f"  ⚠️ 批量插入部分冲突/失败: {e}")
                batch.clear()
        if batch:
            try:
                dst_col.insert_many(batch, ordered=False)
                copied += len(batch)
            except PyMongoError as e:
                print(f"  ⚠️ 末尾批次插入部分冲突/失败: {e}")
        print(f"  ✅ 完成 {col}: 复制 {copied} 条")
        total_copied += copied
    if not args.dry_run:
        print(f"🎉 迁移完成，总复制 {total_copied} 条记录")
    else:
        print("(dry-run) 未执行任何写入")
    return 0

if __name__ == '__main__':
    a = parse_args()
    sys.exit(migrate(a))
