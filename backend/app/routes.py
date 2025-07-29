from flask import request, jsonify, send_file, current_app
from flask import Blueprint
import os
import sys
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from io import BytesIO

# 添加后端目录到系统路径，用于导入数据库工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import get_next_annotation_id


# 加载环境变量，连接MongoDB
load_dotenv()
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://172.20.48.1:27017/local')
MONGO_DB = os.getenv('MONGODB_DB', 'local')
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

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

# 图像样本表结构：
# {
#     image_id: 图像ID,
#     dataset_id: 数据集ID,
#     filename: 文件名
# }
IMAGES = [
    # 数据集1 - 胸片异常检测
    {"image_id": 1, "dataset_id": 1, "filename": "person1_virus_6.jpeg"},
    {"image_id": 2, "dataset_id": 1, "filename": "person1_virus_7.jpeg"},
    {"image_id": 3, "dataset_id": 1, "filename": "person1_virus_8.jpeg"},
    {"image_id": 4, "dataset_id": 1, "filename": "person1_virus_9.jpeg"},
    {"image_id": 5, "dataset_id": 1, "filename": "person3_virus_15.jpeg"},
    {"image_id": 6, "dataset_id": 1, "filename": "person3_virus_16.jpeg"},
    {"image_id": 7, "dataset_id": 1, "filename": "person3_virus_17.jpeg"},
    {"image_id": 8, "dataset_id": 1, "filename": "person8_virus_27.jpeg"},
    {"image_id": 9, "dataset_id": 1, "filename": "person8_virus_28.jpeg"},
    {"image_id": 10, "dataset_id": 1, "filename": "person10_virus_35.jpeg"},
    
    # 数据集2 - CT影像分析  
    {"image_id": 11, "dataset_id": 2, "filename": "person78_bacteria_378.jpeg"},
    {"image_id": 12, "dataset_id": 2, "filename": "person78_bacteria_380.jpeg"},
    {"image_id": 13, "dataset_id": 2, "filename": "person78_bacteria_381.jpeg"},
    {"image_id": 14, "dataset_id": 2, "filename": "person78_bacteria_382.jpeg"},
    {"image_id": 15, "dataset_id": 2, "filename": "person80_bacteria_389.jpeg"},
    {"image_id": 16, "dataset_id": 2, "filename": "person80_bacteria_390.jpeg"},
    {"image_id": 17, "dataset_id": 2, "filename": "person80_bacteria_391.jpeg"},
    {"image_id": 18, "dataset_id": 2, "filename": "person80_bacteria_392.jpeg"},
    {"image_id": 19, "dataset_id": 2, "filename": "person80_bacteria_393.jpeg"},
    {"image_id": 20, "dataset_id": 2, "filename": "person78_bacteria_384.jpeg"}
]

# 标签字典表结构：
# {
#     label_id: 标签ID,
#     dataset_id: 数据集ID,
#     name: 标签名称
# }
LABELS = [
    {"label_id": 1, "dataset_id": 1, "name": "正常"},
    {"label_id": 2, "dataset_id": 1, "name": "异常"},
    {"label_id": 3, "dataset_id": 1, "name": "待定"},
    {"label_id": 1, "dataset_id": 2, "name": "正常"},
    {"label_id": 2, "dataset_id": 2, "name": "异常"},
    {"label_id": 3, "dataset_id": 2, "name": "待定"}
]

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
    # 获取所有数据集列表，根据用户角色返回可访问的数据集
    user_id = request.args.get('user_id')
    
    # 从MongoDB获取数据集
    try:
        datasets = list(db.datasets.find({}, {'_id': 0, 'id': 1, 'name': 1, 'description': 1}))
        
        # 如果没有数据集，返回测试数据集
        if not datasets:
            datasets = [
                {"id": 1, "name": "测试数据集1", "description": "胸片异常检测"},
                {"id": 2, "name": "测试数据集2", "description": "CT影像分析"}
            ]
        
        return jsonify(datasets)
    except Exception as e:
        current_app.logger.error(f"获取数据集失败: {e}")
        # 返回默认测试数据集
        return jsonify([
            {"id": 1, "name": "测试数据集1", "description": "胸片异常检测"},
            {"id": 2, "name": "测试数据集2", "description": "CT影像分析"}
        ])

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
    
    # 根据角色确定实际的expert_id
    actual_expert_id = ROLE_TO_EXPERT_ID.get(role, 2)  # 默认为student
    
    try:
        # 确保ds_id正确处理，支持字符串和整数
        if isinstance(ds_id, str) and ds_id.isdigit():
            ds_id = int(ds_id)
        # 如果ds_id是字符串但不是数字，保持字符串类型
        
        # 从MongoDB获取该数据集下所有图片
        imgs = list(db.images.find({'dataset_id': ds_id}, {'_id': 0}))
        
        # 如果MongoDB中没有图片，使用测试数据
        if not imgs:
            # 对于测试数据，需要处理类型匹配
            if isinstance(ds_id, int):
                imgs = [img for img in IMAGES if img['dataset_id'] == ds_id]
            else:
                # 如果ds_id是字符串，不会在IMAGES中找到匹配项，返回空列表
                imgs = []
            current_app.logger.info(f"使用测试图片数据，数据集 {ds_id}，图片数量: {len(imgs)}")
        else:
            # 为MongoDB中的图片数据添加缺失的image_id字段
            for i, img in enumerate(imgs):
                if 'image_id' not in img:
                    img['image_id'] = i + 1  # 生成一个简单的image_id
            current_app.logger.info(f"使用MongoDB图片数据，数据集 {ds_id}，图片数量: {len(imgs)}")
            
        # 获取该角色的所有标注
        annotations = list(db.annotations.find({
            'dataset_id': ds_id, 
            'expert_id': actual_expert_id
        }, {'_id': 0}))
        
        # 如果MongoDB中没有标注，使用内存数据
        if not annotations:
            if isinstance(ds_id, int):
                annotations = [a for a in ANNOTATIONS if a['dataset_id'] == ds_id and a['expert_id'] == actual_expert_id]
            else:
                annotations = []
        
        current_app.logger.info(f"数据集 {ds_id}，角色 {role}，图片 {len(imgs)} 张，标注 {len(annotations)} 条")
        
        # 合并图片和标注信息
        result = []
        for img in imgs:
            ann = next((a for a in annotations if a['image_id'] == img['image_id']), None)
            
            # 如果有标注，添加标签名称
            if ann:
                # 查找标签名称，支持字符串和整数dataset_id
                label_info = None
                if isinstance(ds_id, int):
                    label_info = next((l for l in LABELS if l['label_id'] == ann.get('label') and l['dataset_id'] == ds_id), None)
                # 对于字符串ds_id，暂时跳过标签名称查找
                if label_info:
                    ann['label_name'] = label_info['name']
            
            img_data = {
                "image_id": img['image_id'], 
                "filename": img['filename'], 
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
    
    # 根据角色确定实际的expert_id
    actual_expert_id = ROLE_TO_EXPERT_ID.get(role, 2)
    
    try:
        # 从MongoDB获取图片
        imgs = list(db.images.find({'dataset_id': dataset_id}, {'_id': 0}))
        
        # 如果没有图片，使用测试数据
        if not imgs:
            imgs = [img for img in IMAGES if img['dataset_id'] == dataset_id]
        else:
            # 为MongoDB中的图片数据添加缺失的image_id字段
            for i, img in enumerate(imgs):
                if 'image_id' not in img:
                    img['image_id'] = i + 1  # 生成一个简单的image_id
        
        # 获取标注
        annotations = list(db.annotations.find({
            'dataset_id': dataset_id,
            'expert_id': actual_expert_id
        }, {'_id': 0}))
        
        if not annotations:
            annotations = [a for a in ANNOTATIONS if a['dataset_id'] == dataset_id and a['expert_id'] == actual_expert_id]
        
        # 合并数据
        result = []
        for img in imgs:
            ann = next((a for a in annotations if a['image_id'] == img['image_id']), None)
            if ann:
                # 在对应数据集中查找标签名称
                label_info = next((l for l in LABELS if l['label_id'] == ann.get('label') and l['dataset_id'] == dataset_id), None)
                if label_info:
                    ann['label_name'] = label_info['name']
            
            result.append({
                "image_id": img['image_id'],
                "filename": img['filename'],
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
    # 获取标签列表接口
    ds_id = request.args.get('dataset_id')
    
    if not ds_id:
        # 如果没有提供dataset_id，返回所有标签
        return jsonify(LABELS)
    
    try:
        # 处理dataset_id，支持字符串和整数
        processed_ds_id = ds_id
        if isinstance(ds_id, str) and ds_id.isdigit():
            processed_ds_id = int(ds_id)
        
        # 尝试从MongoDB获取
        labels_data = list(db.labels.find({"dataset_id": processed_ds_id}, {"_id": 0}))
        
        if labels_data:
            # 按label_id排序确保顺序一致
            labels_data.sort(key=lambda x: x.get('label_id', 0))
            return jsonify(labels_data)
        else:
            # 备用数据 - 从内存中过滤该数据集的标签
            current_app.logger.info(f"数据集 {processed_ds_id} 标签未找到，使用备用数据")
            
            # 对于整数dataset_id，查找匹配的标签
            if isinstance(processed_ds_id, int):
                backup_labels = [l for l in LABELS if l['dataset_id'] == processed_ds_id]
                if backup_labels:
                    backup_labels.sort(key=lambda x: x.get('label_id', 0))
                    return jsonify(backup_labels)
            
            # 默认标签（适用于字符串dataset_id或找不到匹配标签的情况）
            return jsonify([
                {"dataset_id": processed_ds_id, "label_id": 1, "name": "正常"},
                {"dataset_id": processed_ds_id, "label_id": 2, "name": "异常"}
            ])
    
    except Exception as e:
        current_app.logger.error(f"获取标签失败: {e}")
        # 返回默认标签
        processed_ds_id = ds_id
        if isinstance(ds_id, str) and ds_id.isdigit():
            processed_ds_id = int(ds_id)
        
        return jsonify([
            {"dataset_id": processed_ds_id, "label_id": 1, "name": "正常"},
            {"dataset_id": processed_ds_id, "label_id": 2, "name": "异常"}
        ])

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
    # 通用导出接口 - 多工作表Excel文件
    try:
        # 获取当前用户和数据集信息
        expert_id = request.args.get('expert_id')
        dataset_id = request.args.get('dataset_id')
        
        output = BytesIO()
        current_app.logger.info(f"开始导出数据，expert_id: {expert_id}, dataset_id: {dataset_id}")
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. 导出标注数据表 (annotations)
            try:
                current_app.logger.info("正在导出标注数据...")
                annotations_data = list(db.annotations.find({}, {"_id": 0}))
                current_app.logger.info(f"从MongoDB获取到 {len(annotations_data)} 条标注数据")
                
                if not annotations_data:
                    # 使用备用内存数据
                    annotations_data = ANNOTATIONS
                    current_app.logger.info(f"使用备用内存数据: {len(annotations_data)} 条记录")
                
                if annotations_data:
                    # 处理字段名不一致问题：统一使用 label_id
                    for item in annotations_data:
                        if 'label' in item and 'label_id' not in item:
                            item['label_id'] = item['label']
                        item.pop('label', None)  # 移除旧的 label 字段
                    
                    # 按照新的字段顺序排列：dataset_id | record_id | image_id | expert_id | label_id | tip | datetime
                    annotations_df = pd.DataFrame(annotations_data)
                    column_order = ['dataset_id', 'record_id', 'image_id', 'expert_id', 'label_id', 'tip', 'datetime']
                    # 只保留存在的列，并按指定顺序排列
                    available_columns = [col for col in column_order if col in annotations_df.columns]
                    annotations_df = annotations_df.reindex(columns=available_columns)
                    
                    annotations_df.to_excel(writer, sheet_name='annotations', index=False)
                    current_app.logger.info(f"✅ 成功导出标注数据: {len(annotations_df)} 条记录")
                else:
                    # 创建空的标注表结构
                    empty_annotations = pd.DataFrame(columns=['dataset_id', 'record_id', 'image_id', 'expert_id', 'label_id', 'tip', 'datetime'])
                    empty_annotations.to_excel(writer, sheet_name='annotations', index=False)
                    current_app.logger.warning("⚠️ 标注数据为空，创建空表结构")
                    
            except Exception as e:
                current_app.logger.error(f"❌ 导出标注数据失败: {e}")
                # 创建错误信息表
                error_df = pd.DataFrame([{'error': f'标注数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name='annotations', index=False)
            
            # 2. 导出图片数据表 (images)
            try:
                current_app.logger.info("正在导出图片数据...")
                images_data = list(db.images.find({}, {"_id": 0}))
                current_app.logger.info(f"从MongoDB获取到 {len(images_data)} 条图片数据")
                
                if not images_data:
                    # 使用备用内存数据转换为新格式
                    current_app.logger.info("MongoDB中无图片数据，使用备用内存数据")
                    images_data = []
                    for img in IMAGES:
                        images_data.append({
                            'image_id': img['image_id'],
                            'image_path': f"static/img/{img['filename']}"
                        })
                    current_app.logger.info(f"备用数据转换完成: {len(images_data)} 条记录")
                
                if images_data:
                    images_df = pd.DataFrame(images_data)
                    # 确保字段顺序：image_id | image_path
                    column_order = ['image_id', 'image_path']
                    available_columns = [col for col in column_order if col in images_df.columns]
                    images_df = images_df.reindex(columns=available_columns)
                    
                    images_df.to_excel(writer, sheet_name='images', index=False)
                    current_app.logger.info(f"✅ 成功导出图片数据: {len(images_df)} 条记录")
                else:
                    # 创建空的图片表结构
                    empty_images = pd.DataFrame(columns=['image_id', 'image_path'])
                    empty_images.to_excel(writer, sheet_name='images', index=False)
                    current_app.logger.warning("⚠️ 图片数据为空，创建空表结构")
                    
            except Exception as e:
                current_app.logger.error(f"❌ 导出图片数据失败: {e}")
                # 创建错误信息表
                error_df = pd.DataFrame([{'error': f'图片数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name='images', index=False)
            
            # 3. 导出标签数据表 (labels)
            try:
                current_app.logger.info("正在导出标签数据...")
                labels_data = list(db.labels.find({}, {"_id": 0}))
                current_app.logger.info(f"从MongoDB获取到 {len(labels_data)} 条标签数据")
                
                if not labels_data:
                    # 使用备用内存数据转换为新格式
                    current_app.logger.info("MongoDB中无标签数据，使用备用内存数据")
                    labels_data = []
                    label_id_set = set()
                    for label in LABELS:
                        if label['label_id'] not in label_id_set:
                            labels_data.append({
                                'label_id': label['label_id'],
                                'label_name': label['name'],
                                'category': '病理学'  # 默认分类
                            })
                            label_id_set.add(label['label_id'])
                    current_app.logger.info(f"备用数据转换完成: {len(labels_data)} 条记录")
                
                if labels_data:
                    labels_df = pd.DataFrame(labels_data)
                    # 确保字段顺序：label_id | label_name | category
                    column_order = ['label_id', 'label_name', 'category']
                    available_columns = [col for col in column_order if col in labels_df.columns]
                    labels_df = labels_df.reindex(columns=available_columns)
                    
                    # 按label_id排序
                    labels_df = labels_df.sort_values('label_id')
                    
                    labels_df.to_excel(writer, sheet_name='labels', index=False)
                    current_app.logger.info(f"✅ 成功导出标签数据: {len(labels_df)} 条记录")
                else:
                    # 创建空的标签表结构
                    empty_labels = pd.DataFrame(columns=['label_id', 'label_name', 'category'])
                    empty_labels.to_excel(writer, sheet_name='labels', index=False)
                    current_app.logger.warning("⚠️ 标签数据为空，创建空表结构")
                    
            except Exception as e:
                current_app.logger.error(f"❌ 导出标签数据失败: {e}")
                # 创建错误信息表
                error_df = pd.DataFrame([{'error': f'标签数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name='labels', index=False)
        
        output.seek(0)
        
        # 生成文件名
        filename = "medical_annotation_data"
        if dataset_id:
            filename += f"_dataset_{dataset_id}"
        if expert_id:
            filename += f"_{expert_id}"
        filename += ".xlsx"
        
        current_app.logger.info(f"🎉 导出完成，文件名: {filename}")
        
        return send_file(output, 
                        as_attachment=True, 
                        download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        current_app.logger.error(f"❌ 通用导出失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/export_excel/<string:ds_id>')
def export_excel(ds_id):
    # 数据集特定导出接口（支持基于角色的独立数据导出）- 多工作表Excel文件
    expert_id = request.args.get('expert_id')
    
    # 根据用户名获取角色
    user_role = None
    if expert_id:
        for user in USERS:
            if user['username'] == expert_id:
                user_role = user['role']
                break
    
    actual_expert_id = ROLE_TO_EXPERT_ID.get(user_role, 2) if user_role else 2
    
    try:
        # 处理dataset_id，支持字符串和整数
        processed_ds_id = ds_id
        if isinstance(ds_id, str) and ds_id.isdigit():
            processed_ds_id = int(ds_id)
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. 导出标注数据表 (annotations) - 筛选特定数据集和专家
            try:
                if expert_id:
                    # 如果指定了专家，只导出该专家的标注
                    query = {"dataset_id": processed_ds_id, "expert_id": actual_expert_id}
                else:
                    # 否则导出整个数据集的所有标注
                    query = {"dataset_id": processed_ds_id}
                
                annotations_data = list(db.annotations.find(query, {"_id": 0}))
                
                if not annotations_data:
                    # 使用备用内存数据
                    if isinstance(processed_ds_id, int):
                        annotations_data = [a for a in ANNOTATIONS if a.get('dataset_id') == processed_ds_id]
                        if expert_id:
                            annotations_data = [a for a in annotations_data if a.get('expert_id') == actual_expert_id]
                    else:
                        annotations_data = []
                
                if annotations_data:
                    # 按照新的字段顺序排列
                    annotations_df = pd.DataFrame(annotations_data)
                    column_order = ['dataset_id', 'record_id', 'image_id', 'expert_id', 'label_id', 'tip', 'datetime']
                    available_columns = [col for col in column_order if col in annotations_df.columns]
                    annotations_df = annotations_df.reindex(columns=available_columns)
                    
                    annotations_df.to_excel(writer, sheet_name='annotations', index=False)
                    current_app.logger.info(f"导出数据集{processed_ds_id}标注数据: {len(annotations_df)} 条记录")
                else:
                    # 创建空的标注表
                    empty_annotations = pd.DataFrame(columns=['dataset_id', 'record_id', 'image_id', 'expert_id', 'label_id', 'tip', 'datetime'])
                    empty_annotations.to_excel(writer, sheet_name='annotations', index=False)
                    current_app.logger.warning(f"数据集{processed_ds_id}无标注数据")
                    
            except Exception as e:
                current_app.logger.error(f"导出数据集{processed_ds_id}标注数据失败: {e}")
                error_df = pd.DataFrame([{'error': f'标注数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name='annotations', index=False)
            
            # 2. 导出该数据集相关的图片数据表 (images)
            try:
                # 通过关联表查询该数据集的图片
                dataset_images = list(db.image_datasets.find({"dataset_id": processed_ds_id}, {"_id": 0, "image_id": 1}))
                image_ids = [img['image_id'] for img in dataset_images]
                
                if image_ids:
                    # 获取图片详细信息
                    images_data = list(db.images.find({"image_id": {"$in": image_ids}}, {"_id": 0}))
                else:
                    images_data = []
                
                if not images_data:
                    # 使用备用内存数据
                    if isinstance(processed_ds_id, int):
                        backup_images = [img for img in IMAGES if img.get('dataset_id') == processed_ds_id]
                        images_data = []
                        for img in backup_images:
                            images_data.append({
                                'image_id': img['image_id'],
                                'image_path': f"static/img/{img['filename']}"
                            })
                
                if images_data:
                    images_df = pd.DataFrame(images_data)
                    column_order = ['image_id', 'image_path']
                    available_columns = [col for col in column_order if col in images_df.columns]
                    images_df = images_df.reindex(columns=available_columns)
                    
                    images_df.to_excel(writer, sheet_name='images', index=False)
                    current_app.logger.info(f"导出数据集{processed_ds_id}图片数据: {len(images_df)} 条记录")
                else:
                    empty_images = pd.DataFrame(columns=['image_id', 'image_path'])
                    empty_images.to_excel(writer, sheet_name='images', index=False)
                    
            except Exception as e:
                current_app.logger.error(f"导出数据集{processed_ds_id}图片数据失败: {e}")
                error_df = pd.DataFrame([{'error': f'图片数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name='images', index=False)
            
            # 3. 导出标签数据表 (labels) - 导出所有标签供参考
            try:
                labels_data = list(db.labels.find({}, {"_id": 0}))
                if not labels_data:
                    # 使用备用内存数据转换为新格式
                    labels_data = []
                    if isinstance(processed_ds_id, int):
                        backup_labels = [l for l in LABELS if l.get('dataset_id') == processed_ds_id]
                        for label in backup_labels:
                            labels_data.append({
                                'label_id': label['label_id'],
                                'label_name': label['name'],
                                'category': '病理学'  # 默认分类
                            })
                    
                    # 如果仍然没有数据，使用所有LABELS作为备用
                    if not labels_data:
                        label_id_set = set()
                        for label in LABELS:
                            if label['label_id'] not in label_id_set:
                                labels_data.append({
                                    'label_id': label['label_id'],
                                    'label_name': label['name'],
                                    'category': '病理学'
                                })
                                label_id_set.add(label['label_id'])
                
                if labels_data:
                    labels_df = pd.DataFrame(labels_data)
                    column_order = ['label_id', 'label_name', 'category']
                    available_columns = [col for col in column_order if col in labels_df.columns]
                    labels_df = labels_df.reindex(columns=available_columns)
                    
                    # 按label_id排序
                    labels_df = labels_df.sort_values('label_id')
                    
                    labels_df.to_excel(writer, sheet_name='labels', index=False)
                    current_app.logger.info(f"导出标签数据: {len(labels_df)} 条记录")
                else:
                    empty_labels = pd.DataFrame(columns=['label_id', 'label_name', 'category'])
                    empty_labels.to_excel(writer, sheet_name='labels', index=False)
                    
            except Exception as e:
                current_app.logger.error(f"导出标签数据失败: {e}")
                error_df = pd.DataFrame([{'error': f'标签数据导出失败: {str(e)}'}])
                error_df.to_excel(writer, sheet_name='labels', index=False)
        
        output.seek(0)
        
        # 生成文件名
        filename = f"dataset_{processed_ds_id}_medical_data"
        if expert_id:
            filename += f"_{user_role}_role"
        filename += ".xlsx"
        
        return send_file(output, 
                        as_attachment=True, 
                        download_name=filename, 
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        current_app.logger.error(f"数据集{ds_id}导出Excel失败: {e}")
        return jsonify({"error": str(e)}), 500
