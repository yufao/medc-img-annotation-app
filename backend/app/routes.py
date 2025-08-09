from flask import request, jsonify, send_file, current_app, render_template
from flask import Blueprint
import os
import sys
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from io import BytesIO
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 添加后端目录到系统路径，用于导入数据库工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_utils import get_next_annotation_id

# 数据集管理器
from .dataset_manager import dataset_manager


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
    """获取所有数据集列表，支持自动扫描static目录"""
    user_id = request.args.get('user_id')
    
    try:
        # 使用新的数据集管理器获取数据集列表
        datasets = dataset_manager.get_datasets_list()
        
        # 如果没有发现数据集，尝试从MongoDB获取
        if not datasets:
            try:
                datasets = list(db.datasets.find({}, {'_id': 0, 'id': 1, 'name': 1, 'description': 1}))
            except Exception as e:
                current_app.logger.error(f"MongoDB查询失败: {e}")
        
        # 如果仍然没有数据集，返回测试数据集
        if not datasets:
            datasets = [
                {"id": 1, "name": "测试数据集1", "description": "胸片异常检测"},
                {"id": 2, "name": "测试数据集2", "description": "CT影像分析"}
            ]
        
        current_app.logger.info(f"返回数据集列表，共 {len(datasets)} 个数据集")
        return jsonify(datasets)
        
    except Exception as e:
        current_app.logger.error(f"获取数据集失败: {e}")
        # 返回默认测试数据集
        return jsonify([
            {"id": 1, "name": "测试数据集1", "description": "胸片异常检测"},
            {"id": 2, "name": "测试数据集2", "description": "CT影像分析"}
        ])

@bp.route('/api/images_with_annotations', methods=['POST'])
def images_with_annotations():
    """获取数据集图片和标注信息，支持新的编号系统和专属标注集合"""
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
        # 确保ds_id为整数类型
        if isinstance(ds_id, str) and ds_id.isdigit():
            ds_id = int(ds_id)
        
        # 使用新的数据集管理器获取图片信息
        dataset = dataset_manager.get_dataset_by_id(ds_id)
        if not dataset:
            return jsonify({"error": f"数据集 {ds_id} 未找到"}), 404
            
        imgs = dataset['images']
        current_app.logger.info(f"使用数据集管理器获取图片，数据集 {ds_id}，图片数量: {len(imgs)}")
            
        # 获取该数据集专属的标注集合
        annotation_collection = get_annotation_collection(ds_id)
        
        # 获取该角色的所有标注
        annotations = list(annotation_collection.find({
            'expert_id': actual_expert_id
        }, {'_id': 0}))
        
        current_app.logger.info(f"从集合 '{annotation_collection.name}' 获取角色 {role} 的标注 {len(annotations)} 条")
        
        # 合并图片和标注信息
        result = []
        for img in imgs:
            # 在Python端进行匹配
            ann = next((a for a in annotations if a['image_id'] == img['image_id']), None)
            
            # 如果有标注，添加标签名称
            if ann:
                label_info = dataset_manager.get_label_info(ds_id, ann.get('label_id'))
                if label_info:
                    ann['label_name'] = label_info['name']
            
            img_data = {
                "image_id": img['image_id'], 
                "display_id": img.get('display_id', ''),
                "filename": img['filename'],
                "url": img.get('url', f"/static/{dataset['code']}/{img['filename']}"),  # 确保包含完整URL
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
    # 获取标签列表接口 - 重构以支持正确的数据集-标签对应关系
    ds_id = request.args.get('dataset_id')
    
    if not ds_id:
        # 如果没有提供dataset_id，返回空数组而不是所有标签
        current_app.logger.warning("获取标签时未提供dataset_id参数")
        return jsonify([])
    
    try:
        # 处理dataset_id，支持字符串和整数
        processed_ds_id = ds_id
        if isinstance(ds_id, str) and ds_id.isdigit():
            processed_ds_id = int(ds_id)
        
        # 使用数据集管理器获取标签
        labels_data = dataset_manager.get_dataset_labels(processed_ds_id)
        
        if labels_data:
            current_app.logger.info(f"成功获取数据集 {processed_ds_id} 的标签: {len(labels_data)} 个")
            return jsonify(labels_data)
        else:
            current_app.logger.warning(f"数据集 {processed_ds_id} 没有找到任何标签")
            return jsonify([])
    
    except Exception as e:
        current_app.logger.error(f"获取数据集 {ds_id} 标签失败: {e}")
        return jsonify([])

@bp.route('/api/next_image', methods=['POST'])
def next_image():
    # 获取下一个待标注图片接口（基于角色的独立进度）- 修复版本
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
        
        # 使用数据集管理器获取图片信息
        dataset = dataset_manager.get_dataset_by_id(processed_ds_id)
        if not dataset:
            return jsonify({"msg": "error", "error": f"数据集 {processed_ds_id} 未找到"})
        
        imgs = dataset['images']
        
        # 获取该数据集专属的标注集合
        annotation_collection = get_annotation_collection(processed_ds_id)
        
        # 获取该角色已标注的图片ID
        annotated_imgs = list(annotation_collection.find({
            'expert_id': actual_expert_id
        }, {'_id': 0, 'image_id': 1}))
        
        done_img_ids = set([a['image_id'] for a in annotated_imgs])
        
        current_app.logger.info(f"数据集 {processed_ds_id}，角色 {role}，总图片 {len(imgs)} 张，已标注图片ID: {sorted(done_img_ids)}")
        
        # 返回第一个未标注的图片
        for img in sorted(imgs, key=lambda x: x['image_id']):
            if img['image_id'] not in done_img_ids:
                current_app.logger.info(f"角色 {role} 的下一张图片: {img['url']} (image_id: {img['image_id']})")
                return jsonify({
                    "image_id": img['image_id'], 
                    "filename": img['filename'],
                    "url": img.get('url', f"/static/{dataset['code']}/{img['filename']}")
                })
        
        # 全部标注完成
        current_app.logger.info(f"角色 {role} 已完成数据集 {processed_ds_id} 的所有标注")
        return jsonify({"msg": "done"})
        
    except Exception as e:
        current_app.logger.error(f"获取下一张图片失败: {e}")
        return jsonify({"msg": "error", "error": str(e)})

def get_annotation_collection(dataset_id):
    """根据数据集ID获取其专属的MongoDB Collection对象"""
    dataset = dataset_manager.get_dataset_by_id(dataset_id)
    if dataset and 'metadata' in dataset and 'annotation_collection' in dataset['metadata']:
        collection_name = dataset['metadata']['annotation_collection']
        return db[collection_name]
    
    # 备用方案：如果元数据中没有，则使用旧的全局annotations集合
    current_app.logger.warning(f"数据集 {dataset_id} 未找到专属标注集合，将使用全局 'annotations' 集合。")
    return db.annotations

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
        # 获取该数据集专属的标注集合
        annotation_collection = get_annotation_collection(processed_ds_id)

        # 检查是否已经存在该记录
        existing = annotation_collection.find_one({
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
            
            annotation_collection.update_one(
                {'image_id': image_id, 'expert_id': actual_expert_id},
                {"$set": annotation_data}
            )
            current_app.logger.info(f"更新标注: 集合 '{annotation_collection.name}', 角色 {user_role}, 图片 {image_id}, 标签 {label}")
        else:
            # 插入新标注，使用自增序列生成唯一的record_id
            try:
                # 注意：get_next_annotation_id现在可能需要针对不同集合进行管理
                # 为简化，我们暂时继续使用全局计数器，但在大型系统中可能需要调整
                next_record_id = get_next_annotation_id(db)
                annotation_data["record_id"] = next_record_id
                
                annotation_collection.insert_one(annotation_data)
                current_app.logger.info(f"新增标注: 集合 '{annotation_collection.name}', 角色 {user_role}, 图片 {image_id}, 标签 {label}, record_id {next_record_id}")
                
            except Exception as insert_error:
                current_app.logger.error(f"保存标注到集合 '{annotation_collection.name}' 失败: {insert_error}")
                return jsonify({"msg": "error", "error": str(insert_error)}), 500
        
        # (可选) 更新内存数据（用于备用），但这部分逻辑在多集合模式下会变得复杂且不准确
        # 建议未来逐步废弃内存备用方案
        
        return jsonify({"msg": "saved", "expert_id": actual_expert_id})
        
    except Exception as e:
        current_app.logger.error(f"保存标注失败: {e}")
        return jsonify({"msg": "error", "error": str(e)})

@bp.route('/api/update_annotation', methods=['POST'])
def update_annotation():
    # 修改标注接口（支持基于角色的独立标注）- 修复版本，使用专属集合
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
        'label_id': data.get('label'),  # 统一使用label_id
        'tip': data.get('tip', ''),
        'datetime': datetime.now().isoformat()
    }
    
    try:
        # 获取该数据集专属的标注集合
        annotation_collection = get_annotation_collection(processed_ds_id)
        
        # 更新专属集合中的数据
        result = annotation_collection.update_one({
            "image_id": image_id, 
            "expert_id": actual_expert_id
        }, {"$set": update_fields})
        
        if result.modified_count > 0:
            current_app.logger.info(f"更新标注成功: 集合 '{annotation_collection.name}', 角色 {user_role}, 图片 {image_id}")
            return jsonify({"msg": "updated"})
        else:
            return jsonify({"msg": "not found or not changed"})
            
    except Exception as e:
        current_app.logger.error(f"更新标注失败: {e}")
        return jsonify({"msg": "error", "error": str(e)})

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

@bp.route('/api/export_dataset', methods=['GET'])
def export_dataset():
    """导出单个数据集的Excel文件（修复版本，使用专属标注集合）"""
    dataset_id = request.args.get('dataset_id')
    
    if not dataset_id:
        return jsonify({"error": "缺少dataset_id参数"}), 400
    
    try:
        dataset_id = int(dataset_id)
        
        # 获取数据集信息
        dataset = dataset_manager.get_dataset_by_id(dataset_id)
        if not dataset:
            return jsonify({"error": f"数据集 {dataset_id} 未找到"}), 404
        
        # 获取该数据集专属的标注集合
        annotation_collection = get_annotation_collection(dataset_id)
        
        # 从专属集合中获取所有标注数据
        annotations_data = list(annotation_collection.find({}, {"_id": 0}))
        current_app.logger.info(f"从集合 '{annotation_collection.name}' 获取到 {len(annotations_data)} 条标注数据")
        
        # 获取标签映射
        labels_map = {}
        dataset_labels = dataset_manager.get_dataset_labels(dataset_id)
        for label in dataset_labels:
            labels_map[label.get('label_id')] = label.get('name', '未知标签')
        
        # 创建导出数据
        export_data = []
        for image in dataset['images']:
            # 查找该图片的标注
            image_annotations = [a for a in annotations_data if a['image_id'] == image['image_id']]
            
            if image_annotations:
                # 有标注的图片
                for annotation in image_annotations:
                    label_name = labels_map.get(annotation.get('label_id'), '未知标签')
                    export_record = {
                        'dataset_id': dataset_id,
                        'dataset_code': dataset['code'],
                        'dataset_name': dataset['name'],
                        'image_id': image['image_id'],
                        'display_id': image.get('display_id', ''),
                        'seq_in_dataset': image.get('seq_in_dataset', 0),
                        'filename': image['filename'],
                        'label_id': annotation.get('label_id'),
                        'label_name': label_name,
                        'tip': annotation.get('tip', ''),
                        'expert_id': annotation.get('expert_id'),
                        'annotated_at': annotation.get('datetime', ''),
                        'created_at': image.get('created_at', ''),
                        'file_size': image.get('file_size', 0)
                    }
                    export_data.append(export_record)
            else:
                # 未标注的图片
                export_record = {
                    'dataset_id': dataset_id,
                    'dataset_code': dataset['code'],
                    'dataset_name': dataset['name'],
                    'image_id': image['image_id'],
                    'display_id': image.get('display_id', ''),
                    'seq_in_dataset': image.get('seq_in_dataset', 0),
                    'filename': image['filename'],
                    'label_id': None,
                    'label_name': '未标注',
                    'tip': '',
                    'expert_id': None,
                    'annotated_at': '',
                    'created_at': image.get('created_at', ''),
                    'file_size': image.get('file_size', 0)
                }
                export_data.append(export_record)
        
        if not export_data:
            return jsonify({"error": f"数据集 {dataset_id} 无数据可导出"}), 404
        
        # 创建Excel文件
        output = BytesIO()
        df = pd.DataFrame(export_data)
        
        # 字段排序
        column_order = [
            'dataset_id', 'dataset_code', 'dataset_name',
            'image_id', 'display_id', 'seq_in_dataset', 'filename',
            'label_id', 'label_name', 'tip',
            'expert_id', 'annotated_at', 'created_at', 'file_size'
        ]
        available_columns = [col for col in column_order if col in df.columns]
        df = df.reindex(columns=available_columns)
        
        # 按seq_in_dataset排序
        df = df.sort_values('seq_in_dataset')
        
        # 写入Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='dataset_annotations', index=False)
        
        output.seek(0)
        
        # 生成文件名
        dataset_code = dataset['code']
        filename = f"{dataset_code}_annotations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        current_app.logger.info(f"成功导出数据集 {dataset_id} (集合: {annotation_collection.name})，共 {len(export_data)} 条记录")
        
        return send_file(output, 
                        as_attachment=True, 
                        download_name=filename, 
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        current_app.logger.error(f"导出数据集 {dataset_id} 失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/export_all', methods=['GET'])
def export_all_datasets():
    """导出所有数据集的Excel文件（多Sheet格式）"""
    try:
        # 使用数据集管理器获取所有数据集的导出数据
        all_export_data = dataset_manager.get_export_data()
        
        if not all_export_data:
            return jsonify({"error": "未找到任何数据集或数据"}), 404
        
        # 按数据集分组
        datasets_data = {}
        for record in all_export_data:
            dataset_code = record['dataset_code']
            if dataset_code not in datasets_data:
                datasets_data[dataset_code] = []
            datasets_data[dataset_code].append(record)
        
        # 创建Excel文件
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 为每个数据集创建一个Sheet
            for dataset_code, data in datasets_data.items():
                df = pd.DataFrame(data)
                
                # 字段排序
                column_order = [
                    'dataset_id', 'dataset_code', 'dataset_name',
                    'image_id', 'display_id', 'seq_in_dataset', 'filename',
                    'label_id', 'label_name', 'tip',
                    'expert_id', 'annotated_at', 'created_at', 'file_size'
                ]
                available_columns = [col for col in column_order if col in df.columns]
                df = df.reindex(columns=available_columns)
                
                # 按seq_in_dataset排序
                df = df.sort_values('seq_in_dataset')
                
                # 使用数据集代码作为Sheet名称（Excel Sheet名称限制31字符）
                sheet_name = dataset_code[:31] if len(dataset_code) > 31 else dataset_code
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 创建汇总Sheet
            all_df = pd.DataFrame(all_export_data)
            column_order = [
                'dataset_id', 'dataset_code', 'dataset_name',
                'image_id', 'display_id', 'seq_in_dataset', 'filename',
                'label_id', 'label_name', 'tip',
                'expert_id', 'annotated_at', 'created_at', 'file_size'
            ]
            available_columns = [col for col in column_order if col in all_df.columns]
            all_df = all_df.reindex(columns=available_columns)
            all_df = all_df.sort_values(['dataset_id', 'seq_in_dataset'])
            all_df.to_excel(writer, sheet_name='All_Datasets', index=False)
        
        output.seek(0)
        
        # 生成文件名
        filename = f"all_datasets_annotations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        total_records = len(all_export_data)
        total_datasets = len(datasets_data)
        current_app.logger.info(f"成功导出所有数据集，共 {total_datasets} 个数据集，{total_records} 条记录")
        
        return send_file(output, 
                        as_attachment=True, 
                        download_name=filename, 
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        current_app.logger.error(f"导出所有数据集失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/datasets/scan', methods=['POST'])
def scan_datasets():
    """手动触发数据集扫描"""
    try:
        # 强制刷新数据集缓存
        datasets = dataset_manager.scan_datasets(force_refresh=True)
        
        return jsonify({
            "message": "数据集扫描完成",
            "datasets_count": len(datasets),
            "datasets": list(datasets.keys())
        })
    
    except Exception as e:
        current_app.logger.error(f"扫描数据集失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/datasets/<int:dataset_id>/info', methods=['GET'])
def get_dataset_info(dataset_id):
    """获取数据集详细信息"""
    try:
        dataset = dataset_manager.get_dataset_by_id(dataset_id)
        
        if not dataset:
            return jsonify({"error": f"数据集 {dataset_id} 不存在"}), 404
        
        # 返回数据集信息（不包含完整的图片列表以减少响应大小）
        info = {
            'id': dataset['id'],
            'code': dataset['code'],
            'name': dataset['name'],
            'description': dataset['description'],
            'category': dataset.get('category', 'general'),
            'total_images': dataset['total_images'],
            'active': dataset.get('active', True),
            'created_at': dataset.get('created_at'),
            'folder_path': dataset['folder_path'],
            'metadata': dataset.get('metadata', {})
        }
        
        return jsonify(info)
    
    except Exception as e:
        current_app.logger.error(f"获取数据集信息失败: {e}")
        return jsonify({"error": str(e)}), 500

# ============= Admin数据集管理接口 =============

def check_admin_auth(expert_id):
    """检查是否为admin用户"""
    if not expert_id:
        return False
    for user in USERS:
        if user['username'] == expert_id and user['role'] == 'admin':
            return True
    return False

@bp.route('/api/admin/datasets', methods=['GET'])
def admin_get_all_datasets():
    """管理员获取所有数据集（包括未激活的）"""
    expert_id = request.args.get('expert_id')
    
    if not check_admin_auth(expert_id):
        return jsonify({"error": "权限不足，仅管理员可访问"}), 403
    
    try:
        # 强制刷新并获取所有数据集
        datasets = dataset_manager.scan_datasets(force_refresh=True)
        
        # 返回完整信息
        result = []
        for code, dataset in datasets.items():
            result.append({
                'id': dataset['id'],
                'code': dataset['code'],
                'name': dataset['name'],
                'description': dataset['description'],
                'category': dataset.get('category', 'general'),
                'total_images': dataset['total_images'],
                'active': dataset.get('active', True),
                'created_at': dataset.get('created_at'),
                'folder_path': dataset['folder_path'],
                'metadata': dataset.get('metadata', {})
            })
        
        current_app.logger.info(f"管理员 {expert_id} 查看所有数据集，共 {len(result)} 个")
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"管理员获取数据集失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/admin/datasets/<string:code>/toggle', methods=['POST'])
def admin_toggle_dataset(code):
    """管理员切换数据集激活状态"""
    data = request.json
    expert_id = data.get('expert_id')
    active = data.get('active', True)
    
    if not check_admin_auth(expert_id):
        return jsonify({"error": "权限不足，仅管理员可访问"}), 403
    
    try:
        dataset = dataset_manager.get_dataset_by_code(code)
        if not dataset:
            return jsonify({"error": f"数据集 {code} 不存在"}), 404
        
        # 更新元数据
        metadata = dataset.get('metadata', {})
        metadata['active'] = active
        metadata['last_modified'] = datetime.now().isoformat()
        metadata['modified_by'] = expert_id
        
        success = dataset_manager.create_dataset_metadata(code, metadata)
        
        if success:
            action = "激活" if active else "停用"
            current_app.logger.info(f"管理员 {expert_id} {action}数据集 {code}")
            return jsonify({"message": f"数据集 {code} 已{action}"})
        else:
            return jsonify({"error": "更新失败"}), 500
    
    except Exception as e:
        current_app.logger.error(f"切换数据集状态失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/admin/datasets/<string:code>/metadata', methods=['PUT'])
def admin_update_dataset_metadata(code):
    """管理员更新数据集元数据"""
    data = request.json
    expert_id = data.get('expert_id')
    
    if not check_admin_auth(expert_id):
        return jsonify({"error": "权限不足，仅管理员可访问"}), 403
    
    try:
        dataset = dataset_manager.get_dataset_by_code(code)
        if not dataset:
            return jsonify({"error": f"数据集 {code} 不存在"}), 404
        
        # 更新元数据
        metadata = dataset.get('metadata', {})
        
        # 允许更新的字段
        updatable_fields = ['name', 'description', 'category']
        for field in updatable_fields:
            if field in data:
                metadata[field] = data[field]
        
        metadata['last_modified'] = datetime.now().isoformat()
        metadata['modified_by'] = expert_id
        
        success = dataset_manager.create_dataset_metadata(code, metadata)
        
        if success:
            current_app.logger.info(f"管理员 {expert_id} 更新数据集 {code} 元数据")
            return jsonify({"message": f"数据集 {code} 元数据已更新"})
        else:
            return jsonify({"error": "更新失败"}), 500
    
    except Exception as e:
        current_app.logger.error(f"更新数据集元数据失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/admin/datasets/create', methods=['POST'])
def admin_create_dataset():
    """
    管理员创建新数据集。
    此操作会创建文件目录、元数据文件，并在数据库中创建专属的标注集合。
    增加了对孤儿数据库集合的自动清理功能。
    """
    data = request.json
    expert_id = data.get('expert_id')
    
    if not check_admin_auth(expert_id):
        return jsonify({"error": "权限不足，仅管理员可访问"}), 403
    
    try:
        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'general').strip()
        labels = data.get('labels', [])
        
        if not code or not name:
            return jsonify({"error": "数据集代码和名称不能为空"}), 400
        
        if not labels or not isinstance(labels, list):
            return jsonify({"error": "必须提供至少一个标签"}), 400
        
        for i, label in enumerate(labels):
            if not isinstance(label, dict) or not label.get('name', '').strip():
                return jsonify({"error": f"标签 {i+1} 格式错误或名称为空"}), 400
        
        dataset_path = os.path.join(dataset_manager.static_root, code)
        metadata_path = os.path.join(dataset_path, dataset_manager.metadata_filename)
        collection_name = f"annotations_{code}"

        # --- 增强的预检查和自愈逻辑 ---
        collection_exists = collection_name in db.list_collection_names()
        metadata_exists = os.path.exists(metadata_path)

        if dataset_manager.get_dataset_by_code(code) and metadata_exists:
            return jsonify({"error": f"数据集代码 {code} 已完全存在"}), 400

        if collection_exists and not metadata_exists:
            # 发现孤儿集合，自动清理
            db.drop_collection(collection_name)
            current_app.logger.warning(f"发现并已自动删除孤儿数据库集合: {collection_name}")

        # --- 事务性操作开始 ---
        if not os.path.exists(dataset_path):
            os.makedirs(dataset_path, exist_ok=True)
        
        metadata = {
            'name': name,
            'description': description,
            'category': category,
            'active': True,
            'created_at': datetime.now().isoformat(),
            'created_by': expert_id,
            'annotation_collection': collection_name
        }
        
        if not dataset_manager.create_dataset_metadata(code, metadata):
            return jsonify({"error": "创建元数据文件失败"}), 500

        try:
            collection = db.create_collection(collection_name)
            collection.create_index(
                [("image_id", 1), ("expert_id", 1)], 
                unique=True,
                name="image_expert_compound_idx"
            )
            current_app.logger.info(f"成功创建数据库集合 '{collection_name}' 并设置索引。")
        except Exception as db_error:
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            if not os.listdir(dataset_path):
                os.rmdir(dataset_path)
            current_app.logger.error(f"创建数据库集合失败，已回滚文件操作: {db_error}")
            return jsonify({"error": f"数据库操作失败: {db_error}"}), 500

        new_dataset = dataset_manager.get_dataset_by_code(code)
        if not new_dataset:
            return jsonify({"error": "数据集创建后无法在缓存中找到"}), 500
            
        dataset_id = new_dataset['id']
        
        if not dataset_manager.create_dataset_labels(dataset_id, labels):
            current_app.logger.warning(f"数据集 {code} 已创建，但标签创建失败。")
            return jsonify({
                "message": f"数据集 {code} 和数据库集合创建成功，但标签创建失败，请手动添加。",
                "dataset_id": dataset_id,
                "collection_created": collection_name
            }), 201

        current_app.logger.info(f"管理员 {expert_id} 成功创建数据集 {code} (ID: {dataset_id})，包含 {len(labels)} 个标签和数据库集合 '{collection_name}'")
        return jsonify({
            "message": f"数据集 {code}、标签和数据库集合已全部成功创建！",
            "dataset_id": dataset_id,
            "collection_created": collection_name,
            "labels_created": len(labels)
        }), 201

    except Exception as e:
        current_app.logger.error(f"创建数据集的未知错误: {e}")
        return jsonify({"error": str(e)}), 500

# ============= 文件上传管理接口 =============

@bp.route('/api/admin/datasets/<string:code>/upload', methods=['POST'])
def admin_upload_images(code):
    """管理员上传图片到指定数据集"""
    expert_id = request.form.get('expert_id')
    
    if not check_admin_auth(expert_id):
        return jsonify({"error": "权限不足，仅管理员可访问"}), 403
    
    try:
        dataset = dataset_manager.get_dataset_by_code(code)
        if not dataset:
            return jsonify({"error": f"数据集 {code} 不存在"}), 404
        
        if 'files' not in request.files:
            return jsonify({"error": "未选择文件"}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({"error": "未选择有效文件"}), 400
        
        uploaded_files = []
        failed_files = []
        
        for file in files:
            if file and file.filename:
                # 检查文件类型
                filename = file.filename
                _, ext = os.path.splitext(filename.lower())
                
                if ext not in dataset_manager.image_extensions:
                    failed_files.append(f"{filename}: 不支持的文件格式")
                    continue
                
                # 生成安全的文件名
                import uuid
                safe_filename = f"{uuid.uuid4().hex}_{filename}"
                
                # 保存文件
                file_path = os.path.join(dataset['folder_path'], safe_filename)
                try:
                    file.save(file_path)
                    uploaded_files.append(safe_filename)
                    current_app.logger.info(f"上传图片: {safe_filename} 到数据集 {code}")
                except Exception as save_error:
                    failed_files.append(f"{filename}: 保存失败 - {str(save_error)}")
        
        # 刷新数据集缓存
        dataset_manager.scan_datasets(force_refresh=True)
        
        result = {
            "message": f"上传完成",
            "uploaded": len(uploaded_files),
            "failed": len(failed_files),
            "uploaded_files": uploaded_files,
            "failed_files": failed_files
        }
        
        current_app.logger.info(f"管理员 {expert_id} 向数据集 {code} 上传 {len(uploaded_files)} 个文件")
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"上传图片失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/admin/datasets/<string:code>/images', methods=['GET'])
def admin_get_dataset_images(code):
    """管理员获取数据集图片列表"""
    expert_id = request.args.get('expert_id')
    
    if not check_admin_auth(expert_id):
        return jsonify({"error": "权限不足，仅管理员可访问"}), 403
    
    try:
        dataset = dataset_manager.get_dataset_by_code(code)
        if not dataset:
            return jsonify({"error": f"数据集 {code} 不存在"}), 404
        
        images = dataset['images']
        
        # 添加图片预览URL
        for img in images:
            img['preview_url'] = f"/static/{code}/{img['filename']}"
        
        return jsonify({
            "dataset_code": code,
            "dataset_name": dataset['name'],
            "total_images": len(images),
            "images": images
        })
    
    except Exception as e:
        current_app.logger.error(f"获取数据集图片失败: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/admin/datasets/<string:code>/images/<string:filename>', methods=['DELETE'])
def admin_delete_image(code, filename):
    """管理员删除数据集中的图片"""
    data = request.json
    expert_id = data.get('expert_id')
    
    if not check_admin_auth(expert_id):
        return jsonify({"error": "权限不足，仅管理员可访问"}), 403
    
    try:
        dataset = dataset_manager.get_dataset_by_code(code)
        if not dataset:
            return jsonify({"error": f"数据集 {code} 不存在"}), 404
        
        file_path = os.path.join(dataset['folder_path'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": f"文件 {filename} 不存在"}), 404
        
        # 删除文件
        os.remove(file_path)
        
        # 刷新数据集缓存
        dataset_manager.scan_datasets(force_refresh=True)
        
        current_app.logger.info(f"管理员 {expert_id} 删除数据集 {code} 中的图片 {filename}")
        return jsonify({"message": f"图片 {filename} 已删除"})
    
    except Exception as e:
        current_app.logger.error(f"删除图片失败: {e}")
        return jsonify({"error": str(e)}), 500

# ============= 数据集统计接口 =============

@bp.route('/api/admin/statistics', methods=['GET'])
def admin_get_statistics():
    """管理员获取系统统计信息"""
    expert_id = request.args.get('expert_id')
    
    if not check_admin_auth(expert_id):
        return jsonify({"error": "权限不足，仅管理员可访问"}), 403
    
    try:
        datasets = dataset_manager.scan_datasets(force_refresh=True)
        
        # 统计信息
        total_datasets = len(datasets)
        active_datasets = sum(1 for ds in datasets.values() if ds.get('active', True))
        total_images = sum(ds['total_images'] for ds in datasets.values())
        
        # 标注统计
        total_annotations = 0
        annotations_by_role = {'admin': 0, 'doctor': 0, 'student': 0}
        
        try:
            # 从MongoDB获取标注统计
            annotations = list(db.annotations.find({}, {'_id': 0, 'expert_id': 1}))
            if not annotations:
                annotations = ANNOTATIONS
            
            total_annotations = len(annotations)
            
            for ann in annotations:
                expert_id_val = ann.get('expert_id', 2)
                role_name = None
                for role, role_id in ROLE_TO_EXPERT_ID.items():
                    if role_id == expert_id_val:
                        role_name = role
                        break
                
                if role_name and role_name in annotations_by_role:
                    annotations_by_role[role_name] += 1
        
        except Exception as e:
            current_app.logger.warning(f"获取标注统计失败: {e}")
        
        # 按数据集分组的统计
        dataset_stats = []
        for code, dataset in datasets.items():
            ds_annotations = 0
            try:
                ds_annotations = len(list(db.annotations.find({'dataset_id': dataset['id']}, {'_id': 0})))
                if ds_annotations == 0:
                    ds_annotations = len([a for a in ANNOTATIONS if a.get('dataset_id') == dataset['id']])
            except:
                ds_annotations = len([a for a in ANNOTATIONS if a.get('dataset_id') == dataset['id']])
            
            dataset_stats.append({
                'code': code,
                'name': dataset['name'],
                'total_images': dataset['total_images'],
                'total_annotations': ds_annotations,
                'completion_rate': round((ds_annotations / dataset['total_images'] * 100) if dataset['total_images'] > 0 else 0, 2),
                'active': dataset.get('active', True)
            })
        
        result = {
            'system_overview': {
                'total_datasets': total_datasets,
                'active_datasets': active_datasets,
                'total_images': total_images,
                'total_annotations': total_annotations
            },
            'annotations_by_role': annotations_by_role,
            'dataset_statistics': dataset_stats,
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"获取系统统计失败: {e}")
        return jsonify({"error": str(e)}), 500

# ============= Web管理界面 =============

@bp.route('/admin')
def admin_page():
    """管理员Web界面"""
    return render_template('admin.html')

@bp.route('/admin/datasets')
def admin_datasets_page():
    """数据集管理页面"""
    return render_template('admin.html')

# =========================
# 标签管理 API
# =========================

@bp.route('/api/admin/labels/<int:dataset_id>', methods=['GET'])
def get_dataset_labels(dataset_id):
    """获取数据集的标签列表"""
    try:
        labels = dataset_manager.get_dataset_labels(dataset_id)
        return jsonify({"success": True, "labels": labels})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/api/admin/labels', methods=['POST'])
def create_label():
    """创建新标签"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少数据"}), 400
        
        required_fields = ['dataset_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"缺少必要字段: {field}"}), 400
        
        dataset_id = data['dataset_id']
        name = data['name'].strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({"success": False, "error": "标签名称不能为空"}), 400
        
        # 检查标签名是否已存在
        existing_labels = dataset_manager.get_dataset_labels(dataset_id)
        if any(label['name'] == name for label in existing_labels):
            return jsonify({"success": False, "error": "标签名称已存在"}), 400
        
        # 计算新的label_id
        max_id = max([label.get('label_id', 0) for label in existing_labels]) if existing_labels else 0
        new_label_id = max_id + 1
        
        # 创建标签文档
        label_doc = {
            "label_id": new_label_id,
            "dataset_id": dataset_id,
            "name": name,
            "description": description,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        # 保存到数据库
        try:
            db.labels.insert_one(label_doc.copy())
        except Exception as e:
            logger.warning(f"MongoDB保存标签失败，使用内存存储: {e}")
        
        # 保存到内存结构
        memory_label = {
            "label_id": new_label_id,
            "dataset_id": dataset_id,
            "name": name
        }
        LABELS.append(memory_label)
        
        return jsonify({"success": True, "label": label_doc})
        
    except Exception as e:
        logger.error(f"创建标签失败: {e}")
        return jsonify({"success": False, "error": "创建标签失败"}), 500

@bp.route('/api/admin/labels/<int:label_id>', methods=['PUT'])
def update_label(label_id):
    """更新标签"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少数据"}), 400
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({"success": False, "error": "标签名称不能为空"}), 400
        
        # 更新数据库
        update_data = {
            "name": name,
            "description": description,
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            result = db.labels.update_one(
                {"label_id": label_id}, 
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return jsonify({"success": False, "error": "标签不存在"}), 404
                
        except Exception as e:
            logger.warning(f"MongoDB更新标签失败: {e}")
        
        # 更新内存结构
        for label in LABELS:
            if label.get('label_id') == label_id:
                label['name'] = name
                break
        
        return jsonify({"success": True, "message": "标签更新成功"})
        
    except Exception as e:
        logger.error(f"更新标签失败: {e}")
        return jsonify({"success": False, "error": "更新标签失败"}), 500

@bp.route('/api/admin/labels/<int:label_id>', methods=['DELETE'])
def delete_label(label_id):
    """软删除标签"""
    try:
        # 检查标签是否被使用
        try:
            annotation_count = db.annotations.count_documents({"label_id": label_id})
            if annotation_count > 0:
                return jsonify({
                    "success": False, 
                    "error": f"无法删除标签，仍有 {annotation_count} 个标注使用该标签"
                }), 400
        except Exception:
            pass
        
        # 软删除：标记为inactive
        try:
            result = db.labels.update_one(
                {"label_id": label_id}, 
                {"$set": {"active": False, "deleted_at": datetime.now().isoformat()}}
            )
            
            if result.matched_count == 0:
                return jsonify({"success": False, "error": "标签不存在"}), 404
                
        except Exception as e:
            logger.warning(f"MongoDB软删除标签失败: {e}")
        
        # 从内存中移除
        global LABELS
        LABELS = [label for label in LABELS if label.get('label_id') != label_id]
        
        return jsonify({"success": True, "message": "标签删除成功"})
        
    except Exception as e:
        logger.error(f"删除标签失败: {e}")
        return jsonify({"success": False, "error": "删除标签失败"}), 500
