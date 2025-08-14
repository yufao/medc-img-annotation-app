from flask import request, jsonify, send_file, current_app
from flask import Blueprint
import os
import sys
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from io import BytesIO
import uuid
from werkzeug.utils import secure_filename

# 添加后端目录到系统路径，用于导入数据库工具和配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import get_next_annotation_id, get_next_sequence_value
from config import MONGO_URI, MONGO_DB, UPLOAD_FOLDER, MAX_CONTENT_LENGTH

# 连接MongoDB
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # 测试连接
    db = client[MONGO_DB]
    print(f"✅ 数据库连接成功: {MONGO_URI}")
    print(f"✅ 使用数据库: {MONGO_DB}")
    USE_DATABASE = True
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    print("⚠️ 系统将使用内存模式运行，数据不会持久化")
    USE_DATABASE = False
    db = None

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 静态图片目录说明：
# 图片文件应放在 backend/app/static/img/ 目录下
# 前端 <img src="/static/img/xxx.jpg"> 会自动映射到该目录
# Flask 默认会将 static/ 目录作为静态文件根目录

# 用户角色到expert_id的映射
ROLE_TO_EXPERT_ID = {
    "admin": 0,
    "doctor": 1, 
    "student": 2
}

# 用户依然用mock
USERS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "doctor", "password": "doctor123", "role": "doctor"},
    {"username": "student", "password": "student123", "role": "student"},
]
"""
标注记录表结构：
{
    dataset_id: 数据集ID,
    record_id: 标记记录唯一ID,
    image_id: 图像ID,
    expert_id: 区分身份（0=真实标签，1=专家，2=实习医师，3=医学生）, 
    label: 标签ID,
    datetime: 标注时间,
    tip: 备注
}
"""

# 用户角色到expert_id的映射
ROLE_TO_EXPERT_ID = {
    "admin": 0,
    "doctor": 1, 
    "student": 2
}

# 用户依然用mock（用于登录验证）
USERS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "doctor", "password": "doctor123", "role": "doctor"},
    {"username": "student", "password": "student123", "role": "student"},
]

# 内存数据（当数据库不可用时使用）
IMAGES = []
ANNOTATIONS = []

bp = Blueprint('api', __name__)

def register_routes(app):
    # 注册蓝图，将所有API路由挂载到Flask应用
    app.register_blueprint(bp)

@bp.route('/api/login', methods=['POST'])
def login():
    # 用户登录接口，校验用户名和密码，返回用户角色
    data = request.json
    for user in USERS:
        if user['username'] == data.get('username') and user['password'] == data.get('password'):
            return jsonify({"msg": "success", "role": user['role']}), 200
    return jsonify({"msg": "fail"}), 401

@bp.route('/api/datasets', methods=['GET'])
def get_datasets():
    """获取所有数据集列表"""
    user_id = request.args.get('user_id')
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    try:
        datasets = list(db.datasets.find({}, {'_id': 0}))
        current_app.logger.info(f"获取到 {len(datasets)} 个数据集")
        return jsonify(datasets)
    except Exception as e:
        current_app.logger.error(f"获取数据集失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/datasets/<int:dataset_id>/statistics', methods=['GET'])
def get_dataset_statistics(dataset_id):
    """获取指定数据集的统计信息（高效）"""
    expert_id = request.args.get('expert_id')
    role = request.args.get('role', 'student')
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500

    try:
        # 根据角色确定实际的expert_id
        actual_expert_id = ROLE_TO_EXPERT_ID.get(role, 2)

        # 使用 count_documents 进行高效计数
        total_count = db.image_datasets.count_documents({"dataset_id": dataset_id})
        
        annotated_count = db.annotations.count_documents({
            "dataset_id": dataset_id,
            "expert_id": actual_expert_id
        })

        stats = {
            "total_count": total_count,
            "annotated_count": annotated_count
        }
        
        return jsonify(stats)

    except Exception as e:
        current_app.logger.error(f"获取数据集统计失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/admin/datasets', methods=['POST'])
def create_dataset():
    """创建新数据集（仅管理员）"""
    data = request.json
    user_role = data.get('role')
    
    # 权限验证
    if user_role != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    dataset_name = data.get('name')
    dataset_desc = data.get('description', '')
    
    # 验证数据有效性
    if not dataset_name:
        return jsonify({"msg": "error", "error": "数据集名称不能为空"}), 400
    
    try:
        # 使用序列生成唯一的 dataset_id
        next_id = get_next_sequence_value(db, "datasets_id")
        
        # 创建数据集记录
        new_dataset = {
            "id": next_id,
            "name": dataset_name, 
            "description": dataset_desc,
            "created_at": datetime.now().isoformat(),
            "image_count": 0,
            "status": "active"
        }
        
        result = db.datasets.insert_one(new_dataset)
        current_app.logger.info(f"创建数据集成功: {dataset_name}, ID: {next_id}")
        return jsonify({"msg": "success", "dataset_id": next_id}), 201
    except Exception as e:
        current_app.logger.error(f"创建数据集失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/admin/datasets/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    """删除数据集（仅管理员）"""
    user_role = request.args.get('role')
    
    # 权限验证
    if user_role != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    try:
        # 删除数据集记录
        db.datasets.delete_one({"id": dataset_id})
        
        # 查找并删除相关图片ID
        image_links = list(db.image_datasets.find({"dataset_id": dataset_id}))
        image_ids = [link['image_id'] for link in image_links]
        
        # 删除数据集-图片关联
        db.image_datasets.delete_many({"dataset_id": dataset_id})
        
        # 删除标注记录
        db.annotations.delete_many({"dataset_id": dataset_id})
        
        # 注意：不删除图片文件和图片记录，因为可能被其他数据集使用
        
        current_app.logger.info(f"删除数据集成功: ID {dataset_id}, 涉及 {len(image_ids)} 张图片")
        return jsonify({"msg": "success", "deleted_images": len(image_ids)}), 200
    except Exception as e:
        current_app.logger.error(f"删除数据集失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/admin/datasets/<int:dataset_id>/labels', methods=['POST'])
def add_dataset_labels(dataset_id):
    """为数据集添加标签（仅管理员）"""
    data = request.json
    user_role = data.get('role')
    
    # 权限验证
    if user_role != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    labels = data.get('labels', [])
    
    if not labels:
        return jsonify({"msg": "error", "error": "标签列表不能为空"}), 400
    
    try:
        # 获取当前最大label_id
        max_label = db.labels.find_one(sort=[("label_id", -1)])
        next_id = 1
        if max_label:
            next_id = max_label.get('label_id', 0) + 1
        
        # 准备插入的标签数据
        label_records = []
        for i, label in enumerate(labels):
            label_records.append({
                "label_id": next_id + i,
                "label_name": label.get('name'),
                "category": label.get('category', '病理学')
            })
        
        # 批量插入标签
        if label_records:
            result = db.labels.insert_many(label_records)
            current_app.logger.info(f"为数据集 {dataset_id} 添加 {len(result.inserted_ids)} 个标签")
        
        return jsonify({
            "msg": "success", 
            "added_labels": len(label_records),
            "labels": label_records
        }), 201
    except Exception as e:
        current_app.logger.error(f"添加标签失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/admin/datasets/<int:dataset_id>/images', methods=['POST'])
def upload_dataset_images(dataset_id):
    """上传图片到数据集（仅管理员）"""
    user_role = request.form.get('role')
    
    # 权限验证
    if user_role != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    # 检查数据集是否存在
    dataset = db.datasets.find_one({"id": dataset_id})
    if not dataset:
        return jsonify({"msg": "error", "error": f"数据集 {dataset_id} 不存在"}), 404
    
    if 'images' not in request.files:
        return jsonify({"msg": "error", "error": "没有上传图片"}), 400
    
    files = request.files.getlist('images')
    
    if not files or len(files) == 0:
        return jsonify({"msg": "error", "error": "没有选择图片"}), 400
    
    uploaded_images = []
    failed_images = []
    
    try:
        for file in files:
            if file.filename == '':
                continue
            
            # 生成安全的文件名
            original_filename = secure_filename(file.filename)
            # 添加随机字符串避免文件名冲突
            filename = f"{uuid.uuid4().hex}_{original_filename}"
            
            try:
                # 保存文件
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                # 使用序列生成唯一的 image_id
                image_id = get_next_sequence_value(db, "images_id")
                
                # 记录图片信息
                image_record = {
                    "image_id": image_id,
                    "image_path": f"static/img/{filename}"
                }
                
                # 插入图片记录
                db.images.insert_one(image_record)
                
                # 关联图片和数据集
                db.image_datasets.insert_one({
                    "image_id": image_id,
                    "dataset_id": dataset_id
                })
                
                # 添加到上传成功列表
                uploaded_images.append({
                    "image_id": image_id,
                    "filename": filename,
                    "original_name": original_filename
                })
            except Exception as e:
                current_app.logger.error(f"上传图片失败: {file.filename}, 错误: {e}")
                failed_images.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        # 更新数据集图片计数
        db.datasets.update_one(
            {"id": dataset_id},
            {"$inc": {"image_count": len(uploaded_images)}}
        )
        
        current_app.logger.info(f"数据集 {dataset_id} 上传图片: 成功 {len(uploaded_images)}, 失败 {len(failed_images)}")
        
        return jsonify({
            "msg": "success", 
            "uploaded": len(uploaded_images),
            "failed": len(failed_images),
            "images": uploaded_images,
            "errors": failed_images
        }), 201
    except Exception as e:
        current_app.logger.error(f"批量上传图片失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

# 获取指定数据集下所有图片及标注（供选择进入和修改）
@bp.route('/api/images_with_annotations', methods=['POST'])
def images_with_annotations():
    data = request.json
    ds_id = data.get('dataset_id')
    expert_id = data.get('expert_id')
    role = data.get('role', 'student')
    include_all = data.get('include_all', False)
    page = data.get('page', 1)
    page_size = data.get('pageSize', 20)
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    # 根据角色确定实际的expert_id
    actual_expert_id = ROLE_TO_EXPERT_ID.get(role, 2)  # 默认为student
    
    try:
        # 确保ds_id正确处理
        if isinstance(ds_id, str) and ds_id.isdigit():
            ds_id = int(ds_id)
        
        # 从数据集-图片关联表获取该数据集下的图片ID
        dataset_images = list(db.image_datasets.find(
            {"dataset_id": ds_id}, 
            {"_id": 0, "image_id": 1}
        ))
        
        if not dataset_images:
            current_app.logger.warning(f"数据集 {ds_id} 中没有图片")
            return jsonify([])
        
        image_ids = [img['image_id'] for img in dataset_images]
        
        # 获取图片详细信息
        imgs = list(db.images.find(
            {"image_id": {"$in": image_ids}}, 
            {"_id": 0}
        ))
        
        current_app.logger.info(f"数据集 {ds_id} 中有 {len(imgs)} 张图片")
        
        # 获取该角色在此数据集的所有标注
        annotations = list(db.annotations.find({
            'dataset_id': ds_id, 
            'expert_id': actual_expert_id
        }, {'_id': 0}))
        
        current_app.logger.info(f"用户 {role} 在数据集 {ds_id} 中有 {len(annotations)} 条标注")
        
        # 获取标签信息用于显示标签名称
        labels = list(db.labels.find({}, {"_id": 0}))
        labels_dict = {label['label_id']: label.get('label_name', '') for label in labels}
        
        # 合并图片和标注信息
        result = []
        for img in imgs:
            ann = next((a for a in annotations if a['image_id'] == img['image_id']), None)
            
            # 如果有标注，添加标签名称
            if ann and ann.get('label_id'):
                ann['label_name'] = labels_dict.get(ann['label_id'], '')
            
            img_data = {
                "image_id": img['image_id'], 
                "filename": img.get('image_path', '').split('/')[-1],  # 从路径中提取文件名
                "image_path": img.get('image_path', ''),
                "annotation": ann
            }
            
            # 如果include_all为False，只返回未标注的图片
            if include_all or not ann:
                result.append(img_data)
        
        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_result = result[start_idx:end_idx]
        
        return jsonify(paginated_result)
        
    except Exception as e:
        current_app.logger.error(f"获取图片标注失败: {e}")
        return jsonify([])

# 添加新的API端点：获取数据集图片（备用方案）
@bp.route('/api/datasets/<int:dataset_id>/images', methods=['GET'])
def get_dataset_images(dataset_id):
    expert_id = request.args.get('expert_id')
    role = request.args.get('role', 'student')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 20))
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    # 根据角色确定实际的expert_id
    actual_expert_id = ROLE_TO_EXPERT_ID.get(role, 2)
    
    try:
        # 从数据集-图片关联表获取该数据集下的图片ID
        dataset_images = list(db.image_datasets.find(
            {"dataset_id": dataset_id}, 
            {"_id": 0, "image_id": 1}
        ))
        
        if not dataset_images:
            return jsonify([])
        
        image_ids = [img['image_id'] for img in dataset_images]
        
        # 获取图片详细信息
        imgs = list(db.images.find(
            {"image_id": {"$in": image_ids}}, 
            {"_id": 0}
        ))
        
        # 获取标注
        annotations = list(db.annotations.find({
            'dataset_id': dataset_id,
            'expert_id': actual_expert_id
        }, {'_id': 0}))
        
        # 获取标签信息
        labels = list(db.labels.find({}, {"_id": 0}))
        labels_dict = {label['label_id']: label.get('label_name', '') for label in labels}
        
        # 合并数据
        result = []
        for img in imgs:
            ann = next((a for a in annotations if a['image_id'] == img['image_id']), None)
            if ann and ann.get('label_id'):
                ann['label_name'] = labels_dict.get(ann['label_id'], '')
            
            result.append({
                "image_id": img['image_id'],
                "filename": img.get('image_path', '').split('/')[-1],
                "image_path": img.get('image_path', ''),
                "annotation": ann
            })
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_result = result[start_idx:end_idx]
        
        return jsonify(paginated_result)
        
    except Exception as e:
        current_app.logger.error(f"获取数据集图片失败: {e}")
        return jsonify([])

# 获取上一张图片（根据当前图片ID）
@bp.route('/api/prev_image', methods=['POST'])
def prev_image():
    data = request.json
    ds_id = data.get('dataset_id')
    curr_image_id = data.get('image_id')
    
    try:
        imgs = list(db.images.find({'dataset_id': ds_id}, {'_id': 0}))
        
        # 为MongoDB中的图片数据添加缺失的image_id字段
        for i, img in enumerate(imgs):
            if 'image_id' not in img:
                img['image_id'] = i + 1  # 生成一个简单的image_id
        
        # 如果没有图片，使用测试数据
        if not imgs:
            if isinstance(ds_id, int):
                imgs = [img for img in IMAGES if img['dataset_id'] == ds_id]
            else:
                imgs = []
        
        imgs_sorted = sorted(imgs, key=lambda x: x['image_id'])
        prev_img = None
        for i, img in enumerate(imgs_sorted):
            if img['image_id'] == curr_image_id and i > 0:
                prev_img = imgs_sorted[i-1]
                break
        if prev_img:
            return jsonify(prev_img)
        else:
            return jsonify({"msg": "no previous image"})
            
    except Exception as e:
        current_app.logger.error(f"获取上一张图片失败: {e}")
        return jsonify({"msg": "error"})
    
    
@bp.route('/api/labels', methods=['GET'])
def get_labels():
    """获取标签列表接口"""
    ds_id = request.args.get('dataset_id')
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    try:
        # 处理dataset_id，支持字符串和整数
        if ds_id:
            processed_ds_id = ds_id
            if isinstance(ds_id, str) and ds_id.isdigit():
                processed_ds_id = int(ds_id)
            
            # 尝试从MongoDB获取特定数据集的标签
            labels_data = list(db.labels.find({"dataset_id": processed_ds_id}, {"_id": 0}))
            
            # 如果没有找到特定数据集的标签，返回所有标签（兼容旧数据）
            if not labels_data:
                current_app.logger.info(f"数据集 {processed_ds_id} 没有专用标签，使用通用标签")
                labels_data = list(db.labels.find({}, {"_id": 0}))
        else:
            # 如果没有提供dataset_id，返回所有标签
            labels_data = list(db.labels.find({}, {"_id": 0}))
        
        # 标准化标签数据格式，确保兼容性
        standardized_labels = []
        for label in labels_data:
            standardized_label = {
                "label_id": label.get("label_id"),
                "name": label.get("name") or label.get("label_name"),  # 兼容两种字段名
                "dataset_id": label.get("dataset_id", processed_ds_id if ds_id else None)
            }
            standardized_labels.append(standardized_label)
        
        # 按label_id排序确保顺序一致
        standardized_labels.sort(key=lambda x: x.get('label_id', 0))
        
        current_app.logger.info(f"返回标签数据: {len(standardized_labels)} 个标签")
        return jsonify(standardized_labels)
        
    except Exception as e:
        current_app.logger.error(f"获取标签失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

@bp.route('/api/next_image', methods=['POST'])
def next_image():
    # 获取下一个待标注图片接口（基于角色的独立进度）
    data = request.json
    ds_id = data.get('dataset_id')
    expert_id = data.get('expert_id')
    role = data.get('role', 'student')
    
    # 根据角色确定实际的expert_id
    actual_expert_id = ROLE_TO_EXPERT_ID.get(role, 2)
    
    try:
        # 处理dataset_id，支持字符串和整数
        processed_ds_id = ds_id
        if isinstance(ds_id, str) and ds_id.isdigit():
            processed_ds_id = int(ds_id)
        
        # 从MongoDB获取该数据集下所有图片
        imgs = list(db.images.find({'dataset_id': processed_ds_id}, {'_id': 0}))
        
        # 如果MongoDB中没有图片，使用测试数据
        if not imgs:
            if isinstance(processed_ds_id, int):
                imgs = [img for img in IMAGES if img['dataset_id'] == processed_ds_id]
            else:
                imgs = []  # 字符串dataset_id在测试数据中找不到匹配项
        else:
            # 为MongoDB中的图片数据添加缺失的image_id字段
            for i, img in enumerate(imgs):
                if 'image_id' not in img:
                    img['image_id'] = i + 1  # 生成一个简单的image_id
        
        # 获取该角色已标注的图片ID
        annotated_imgs = list(db.annotations.find({
            'dataset_id': processed_ds_id, 
            'expert_id': actual_expert_id
        }, {'_id': 0, 'image_id': 1}))
        
        # 如果MongoDB中没有标注，使用内存数据
        if not annotated_imgs:
            if isinstance(processed_ds_id, int):
                annotated_imgs = [{'image_id': a.get('image_id')} for a in ANNOTATIONS 
                                if a.get('dataset_id') == processed_ds_id and a.get('expert_id') == actual_expert_id]
            else:
                annotated_imgs = []
        
        done_img_ids = set([a['image_id'] for a in annotated_imgs])
        
        current_app.logger.info(f"数据集{processed_ds_id}，角色{role}，总图片{len(imgs)}张，已标注图片ID: {sorted(done_img_ids)}")
        
        # 返回第一个未标注的图片
        for img in sorted(imgs, key=lambda x: x['image_id']):
            if img['image_id'] not in done_img_ids:
                current_app.logger.info(f"角色 {role} 的下一张图片: static/img/{img['filename']} (image_id: {img['image_id']})")
                return jsonify({"image_id": img['image_id'], "filename": img['filename']})
        
        # 全部标注完成
        current_app.logger.info(f"角色 {role} 已完成数据集 {processed_ds_id} 的所有标注")
        return jsonify({"msg": "done"})
        
    except Exception as e:
        current_app.logger.error(f"获取下一张图片失败: {e}")
        return jsonify({"msg": "error"})

@bp.route('/api/annotate', methods=['POST'])
def annotate():
    # 提交标注结果接口（支持基于角色的独立标注）
    data = request.json
    ds_id = data.get('dataset_id')
    image_id = data.get('image_id')
    expert_id = data.get('expert_id')
    label = data.get('label')
    tip = data.get('tip', '')
    
    # 处理dataset_id，支持字符串和整数
    processed_ds_id = ds_id
    if isinstance(ds_id, str) and ds_id.isdigit():
        processed_ds_id = int(ds_id)
    
    # 根据用户名获取角色，再确定实际的expert_id
    user_role = None
    for user in USERS:
        if user['username'] == expert_id:
            user_role = user['role']
            break
    
    actual_expert_id = ROLE_TO_EXPERT_ID.get(user_role, 2) if user_role else 2
    
    try:
        # 检查是否已经存在该记录
        existing = db.annotations.find_one({
            'dataset_id': processed_ds_id,
            'image_id': image_id,
            'expert_id': actual_expert_id
        })
        
        annotation_data = {
            "dataset_id": processed_ds_id,
            "image_id": image_id,
            "expert_id": actual_expert_id,
            "label_id": label,  # 统一使用 label_id
            "datetime": datetime.now().isoformat(),
            "tip": tip
        }
        
        if existing:
            # 更新现有标注，不需要生成新的record_id
            annotation_data["record_id"] = existing.get("record_id")  # 保持原有的record_id
            
            db.annotations.update_one(
                {
                    'dataset_id': processed_ds_id,
                    'image_id': image_id,
                    'expert_id': actual_expert_id
                },
                {"$set": annotation_data}
            )
            current_app.logger.info(f"更新标注: 角色{user_role}, 图片{image_id}, 标签{label}")
        else:
            # 插入新标注，使用自增序列生成唯一的record_id
            try:
                next_record_id = get_next_annotation_id(db)
                annotation_data["record_id"] = next_record_id
                
                db.annotations.insert_one(annotation_data)
                current_app.logger.info(f"新增标注: 角色{user_role}, 图片{image_id}, 标签{label}, record_id{next_record_id}")
                
            except Exception as insert_error:
                current_app.logger.error(f"保存标注失败: {insert_error}")
                return jsonify({"msg": "error", "error": str(insert_error)}), 500
        
        # 同时更新内存数据（用于备用）
        # 移除旧的标注记录
        ANNOTATIONS[:] = [a for a in ANNOTATIONS if not (
            a.get('dataset_id') == processed_ds_id and 
            a.get('image_id') == image_id and 
            a.get('expert_id') == actual_expert_id
        )]
        # 添加新的标注记录（统一字段名）
        memory_annotation = annotation_data.copy()
        memory_annotation['label'] = label  # 为了向后兼容，同时保留label字段
        ANNOTATIONS.append(memory_annotation)
        
        return jsonify({"msg": "saved", "expert_id": actual_expert_id})
        
    except Exception as e:
        current_app.logger.error(f"保存标注失败: {e}")
        # 备用方案：直接存储到内存
        try:
            # 生成简单的record_id用于内存存储
            max_memory_id = max([a.get('record_id', 0) for a in ANNOTATIONS], default=0)
            annotation_data["record_id"] = max_memory_id + 1
            
            # 移除旧记录
            ANNOTATIONS[:] = [a for a in ANNOTATIONS if not (
                a.get('dataset_id') == processed_ds_id and 
                a.get('image_id') == image_id and 
                a.get('expert_id') == actual_expert_id
            )]
            
            # 添加新记录（保持向后兼容）
            memory_annotation = annotation_data.copy()
            memory_annotation['label'] = label
            ANNOTATIONS.append(memory_annotation)
            
            current_app.logger.info(f"备用存储成功: 角色{user_role}, 图片{image_id}, 标签{label}")
            return jsonify({"msg": "saved"})
        except Exception as fallback_error:
            current_app.logger.error(f"备用存储也失败: {fallback_error}")
            return jsonify({"msg": "error", "error": str(e)})

@bp.route('/api/update_annotation', methods=['POST'])
def update_annotation():
    # 修改标注接口（支持基于角色的独立标注）
    data = request.json
    ds_id = data.get('dataset_id')
    image_id = data.get('image_id')
    expert_id = data.get('expert_id')
    
    # 处理dataset_id，支持字符串和整数
    processed_ds_id = ds_id
    if isinstance(ds_id, str) and ds_id.isdigit():
        processed_ds_id = int(ds_id)
    
    # 根据用户名获取角色
    user_role = None
    for user in USERS:
        if user['username'] == expert_id:
            user_role = user['role']
            break
    
    actual_expert_id = ROLE_TO_EXPERT_ID.get(user_role, 2) if user_role else 2
    
    update_fields = {
        'label': data.get('label'),
        'tip': data.get('tip', ''),
        'datetime': datetime.now().isoformat()
    }
    
    try:
        # 更新MongoDB中的数据
        result = db.annotations.update_one({
            "dataset_id": processed_ds_id, 
            "image_id": image_id, 
            "expert_id": actual_expert_id
        }, {"$set": update_fields})
        
        # 同时更新内存数据
        for ann in ANNOTATIONS:
            if (ann['dataset_id'] == processed_ds_id and 
                ann['image_id'] == image_id and 
                ann['expert_id'] == actual_expert_id):
                ann.update(update_fields)
                break
        
        if result.modified_count or any(a['dataset_id'] == processed_ds_id and a['image_id'] == image_id 
                                       and a['expert_id'] == actual_expert_id for a in ANNOTATIONS):
            current_app.logger.info(f"更新标注成功: 角色{user_role}, 图片{image_id}")
            return jsonify({"msg": "updated"})
        else:
            return jsonify({"msg": "not found or not changed"})
            
    except Exception as e:
        current_app.logger.error(f"更新标注失败: {e}")
        return jsonify({"msg": "error"})

@bp.route('/api/export', methods=['GET'])
def export():
    """改进的导出接口 - 按数据集分别导出，支持筛选"""
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    try:
        # 获取查询参数
        dataset_id = request.args.get('dataset_id')
        expert_id = request.args.get('expert_id')
        
        # 查询用户角色
        user_role = None
        if expert_id:
            for user in USERS:
                if user['username'] == expert_id:
                    user_role = user['role']
                    break
                    
        actual_expert_id = ROLE_TO_EXPERT_ID.get(user_role, 2) if user_role else None
        
        # 处理dataset_id
        if dataset_id and dataset_id.isdigit():
            processed_ds_id = int(dataset_id)
        else:
            processed_ds_id = None
            
        output = BytesIO()
        current_app.logger.info(f"开始导出数据，expert_id: {expert_id}, dataset_id: {dataset_id}")
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 构建查询条件
            query = {}
            if processed_ds_id is not None:
                query['dataset_id'] = processed_ds_id
            if actual_expert_id is not None:
                query['expert_id'] = actual_expert_id
                
            # 1. 导出标注数据
            try:
                current_app.logger.info(f"导出标注数据，查询条件: {query}")
                
                # 从MongoDB获取符合条件的标注
                annotations_data = list(db.annotations.find(query, {"_id": 0}))
                current_app.logger.info(f"从MongoDB获取到 {len(annotations_data)} 条标注数据")
                
                if annotations_data:
                    # 统一标签字段名
                    for item in annotations_data:
                        if 'label' in item and 'label_id' not in item:
                            item['label_id'] = item['label']
                        item.pop('label', None)
                    
                    # 获取标签名称
                    labels_dict = {}
                    all_labels = list(db.labels.find({}, {"_id": 0}))
                        
                    for label in all_labels:
                        labels_dict[label.get('label_id')] = label.get('label_name', '')
                    
                    # 添加标签名称列
                    for item in annotations_data:
                        item['label_name'] = labels_dict.get(item.get('label_id'), '')
                    
                    # 按照指定字段顺序排列
                    annotations_df = pd.DataFrame(annotations_data)
                    column_order = ['dataset_id', 'record_id', 'image_id', 'expert_id', 
                                   'label_id', 'label_name', 'tip', 'datetime']
                    available_columns = [col for col in column_order if col in annotations_df.columns]
                    annotations_df = annotations_df.reindex(columns=available_columns)
                    
                    # 按数据集和记录ID排序
                    if 'dataset_id' in annotations_df.columns:
                        annotations_df = annotations_df.sort_values(['dataset_id', 'record_id'])
                    
                    sheet_name = f"标注数据"
                    if processed_ds_id:
                        sheet_name = f"数据集{processed_ds_id}标注"
                    
                    annotations_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    current_app.logger.info(f"✅ 成功导出标注数据: {len(annotations_df)} 条记录")
                else:
                    # 创建空表
                    empty_annotations = pd.DataFrame(columns=['dataset_id', 'record_id', 'image_id', 
                                                            'expert_id', 'label_id', 'label_name', 
                                                            'tip', 'datetime'])
                    sheet_name = "标注数据"
                    if processed_ds_id:
                        sheet_name = f"数据集{processed_ds_id}标注"
                        
                    empty_annotations.to_excel(writer, sheet_name=sheet_name, index=False)
                    current_app.logger.warning("⚠️ 无符合条件的标注数据，创建空表")
                
            except Exception as e:
                current_app.logger.error(f"❌ 导出标注数据失败: {e}")
                error_df = pd.DataFrame([{'error': f'标注数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name="标注数据错误", index=False)
            
            # 2. 导出图片数据
            try:
                # 构建图片查询条件
                img_query = {}
                
                # 如果指定了数据集，获取该数据集关联的图片ID
                if processed_ds_id is not None:
                    dataset_images = list(db.image_datasets.find(
                        {"dataset_id": processed_ds_id}, 
                        {"_id": 0, "image_id": 1}
                    ))
                    if dataset_images:
                        image_ids = [img['image_id'] for img in dataset_images]
                        img_query["image_id"] = {"$in": image_ids}
                
                current_app.logger.info(f"导出图片数据，查询条件: {img_query}")
                
                # 从MongoDB获取符合条件的图片
                images_data = list(db.images.find(img_query, {"_id": 0}))
                current_app.logger.info(f"从MongoDB获取到 {len(images_data)} 条图片数据")
                
                if images_data:
                    images_df = pd.DataFrame(images_data)
                    column_order = ['image_id', 'image_path']
                    available_columns = [col for col in column_order if col in images_df.columns]
                    images_df = images_df.reindex(columns=available_columns)
                    
                    sheet_name = "图片数据"
                    if processed_ds_id:
                        sheet_name = f"数据集{processed_ds_id}图片"
                        
                    images_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    current_app.logger.info(f"✅ 成功导出图片数据: {len(images_df)} 条记录")
                else:
                    # 创建空表
                    empty_images = pd.DataFrame(columns=['image_id', 'image_path'])
                    
                    sheet_name = "图片数据"
                    if processed_ds_id:
                        sheet_name = f"数据集{processed_ds_id}图片"
                        
                    empty_images.to_excel(writer, sheet_name=sheet_name, index=False)
                    current_app.logger.warning("⚠️ 无符合条件的图片数据，创建空表")
                
            except Exception as e:
                current_app.logger.error(f"❌ 导出图片数据失败: {e}")
                error_df = pd.DataFrame([{'error': f'图片数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name="图片数据错误", index=False)
            
            # 3. 导出标签数据
            try:
                # 构建标签查询条件
                label_query = {}
                
                current_app.logger.info(f"导出标签数据，查询条件: {label_query}")
                
                # 从MongoDB获取符合条件的标签
                labels_data = list(db.labels.find(label_query, {"_id": 0}))
                current_app.logger.info(f"从MongoDB获取到 {len(labels_data)} 条标签数据")
                
                if labels_data:
                    labels_df = pd.DataFrame(labels_data)
                    column_order = ['label_id', 'label_name', 'category']
                    available_columns = [col for col in column_order if col in labels_df.columns]
                    labels_df = labels_df.reindex(columns=available_columns)
                    
                    # 按标签ID排序
                    labels_df = labels_df.sort_values('label_id')
                    
                    sheet_name = "标签数据"
                    if processed_ds_id:
                        sheet_name = f"数据集{processed_ds_id}标签"
                        
                    labels_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    current_app.logger.info(f"✅ 成功导出标签数据: {len(labels_df)} 条记录")
                else:
                    # 创建空表
                    empty_labels = pd.DataFrame(columns=['label_id', 'label_name', 'category'])
                    
                    sheet_name = "标签数据"
                    if processed_ds_id:
                        sheet_name = f"数据集{processed_ds_id}标签"
                        
                    empty_labels.to_excel(writer, sheet_name=sheet_name, index=False)
                    current_app.logger.warning("⚠️ 无符合条件的标签数据，创建空表")
                
            except Exception as e:
                current_app.logger.error(f"❌ 导出标签数据失败: {e}")
                error_df = pd.DataFrame([{'error': f'标签数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name="标签数据错误", index=False)
            
            # 4. 导出数据集数据
            try:
                # 构建数据集查询条件
                ds_query = {}
                if processed_ds_id is not None:
                    ds_query['id'] = processed_ds_id
                
                current_app.logger.info(f"导出数据集信息，查询条件: {ds_query}")
                
                # 从MongoDB获取符合条件的数据集
                datasets_data = list(db.datasets.find(ds_query, {"_id": 0}))
                current_app.logger.info(f"从MongoDB获取到 {len(datasets_data)} 条数据集信息")
                
                if datasets_data:
                    datasets_df = pd.DataFrame(datasets_data)
                    column_order = ['id', 'name', 'description', 'created_at', 'image_count', 'status']
                    available_columns = [col for col in column_order if col in datasets_df.columns]
                    datasets_df = datasets_df.reindex(columns=available_columns)
                    
                    # 按ID排序
                    datasets_df = datasets_df.sort_values('id')
                    
                    datasets_df.to_excel(writer, sheet_name="数据集信息", index=False)
                    current_app.logger.info(f"✅ 成功导出数据集信息: {len(datasets_df)} 条记录")
                else:
                    # 创建空表
                    empty_datasets = pd.DataFrame(columns=['id', 'name', 'description', 'created_at', 'image_count', 'status'])
                    empty_datasets.to_excel(writer, sheet_name="数据集信息", index=False)
                    current_app.logger.warning("⚠️ 无符合条件的数据集信息，创建空表")
                
            except Exception as e:
                current_app.logger.error(f"❌ 导出数据集信息失败: {e}")
                error_df = pd.DataFrame([{'error': f'数据集信息导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name="数据集信息错误", index=False)
        
        output.seek(0)
        
        # 生成文件名
        filename = "医学图像标注数据"
        if processed_ds_id:
            filename += f"_数据集{processed_ds_id}"
        if expert_id:
            filename += f"_{expert_id}"
        filename += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        current_app.logger.info(f"🎉 导出完成，文件名: {filename}")
        
        return send_file(
            output, 
            as_attachment=True, 
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        current_app.logger.error(f"❌ 通用导出失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

# 获取数据集特定标签
@bp.route('/api/admin/datasets/<int:dataset_id>/labels', methods=['GET'])
def get_dataset_labels(dataset_id):
    """获取指定数据集的标签（管理员）"""
    user_role = request.args.get('role')
    
    # 权限验证
    if user_role != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    try:
        # 先查找特定数据集的标签
        dataset_labels = list(db.labels.find({"dataset_id": dataset_id}, {"_id": 0}))
        
        # 如果没有找到，检查是否使用通用标签
        if not dataset_labels:
            # 获取通用标签
            dataset_labels = list(db.labels.find({"dataset_id": None}, {"_id": 0}))
            current_app.logger.info(f"数据集 {dataset_id} 没有专用标签，使用通用标签")
        
        return jsonify(dataset_labels)
        
    except Exception as e:
        current_app.logger.error(f"获取数据集标签失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

# 更新数据集标签
@bp.route('/api/admin/datasets/<int:dataset_id>/labels', methods=['PUT'])
def update_dataset_labels(dataset_id):
    """更新数据集标签（管理员）"""
    data = request.json
    user_role = data.get('role')
    
    # 权限验证
    if user_role != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    labels = data.get('labels', [])
    
    try:
        # 删除该数据集所有现有标签
        db.labels.delete_many({"dataset_id": dataset_id})
        
        # 插入新标签
        if labels:
            # 获取当前最大label_id
            max_label = db.labels.find_one(sort=[("label_id", -1)])
            next_id = 1
            if max_label:
                next_id = max_label.get('label_id', 0) + 1
                
            # 准备插入的标签数据
            label_records = []
            for i, label in enumerate(labels):
                label_records.append({
                    "label_id": next_id + i,
                    "label_name": label.get('name'),
                    "category": label.get('category', '病理学'),
                    "dataset_id": dataset_id
                })
            
            # 批量插入标签
            if label_records:
                result = db.labels.insert_many(label_records)
                current_app.logger.info(f"更新数据集 {dataset_id} 标签：添加 {len(result.inserted_ids)} 个标签")
        
        return jsonify({
            "msg": "success", 
            "updated_labels": len(labels)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"更新标签失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

# 修正数据集图片计数
@bp.route('/api/admin/datasets/<int:dataset_id>/recount', methods=['POST'])
def recount_dataset_images(dataset_id):
    """重新计算数据集图片数量（修正统计错误）"""
    user_role = request.json.get('role')
    
    # 权限验证
    if user_role != 'admin':
        return jsonify({"msg": "error", "error": "权限不足"}), 403
    
    if not USE_DATABASE:
        return jsonify({"msg": "error", "error": "数据库连接不可用"}), 500
    
    try:
        # 计算实际图片数量
        actual_count = db.image_datasets.count_documents({"dataset_id": dataset_id})
        
        # 更新数据集记录
        db.datasets.update_one(
            {"id": dataset_id},
            {"$set": {"image_count": actual_count}}
        )
        
        current_app.logger.info(f"数据集 {dataset_id} 图片数量重新计算: {actual_count} 张")
        
        return jsonify({
            "msg": "success", 
            "dataset_id": dataset_id,
            "image_count": actual_count
        })
        
    except Exception as e:
        current_app.logger.error(f"重新计算图片数量失败: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500
