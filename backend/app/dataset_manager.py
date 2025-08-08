"""
数据集自动发现和管理模块
支持目录扫描式数据集扩展，零代码新增数据集
"""
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatasetManager:
    """数据集管理器 - 支持目录扫描式自动发现"""
    
    def __init__(self, static_root: str = None):
        """
        初始化数据集管理器
        
        Args:
            static_root: 静态文件根目录，默认为 app/static
        """
        if static_root is None:
            # 获取当前文件所在目录的static路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            static_root = os.path.join(current_dir, 'static')
        
        self.static_root = static_root
        self.datasets_cache = {}
        self.images_cache = {}
        self.last_scan_time = None
        
        # 支持的图片格式
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        
        # 元数据文件名
        self.metadata_filename = 'dataset_info.json'
        
        logger.info(f"数据集管理器初始化，静态根目录: {static_root}")
    
    def scan_datasets(self, force_refresh: bool = False) -> Dict:
        """
        扫描静态目录，自动发现数据集
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            Dict: 数据集字典 {dataset_code: dataset_info}
        """
        current_time = datetime.now()
        
        # 如果缓存有效且不强制刷新，直接返回缓存
        if (not force_refresh and 
            self.last_scan_time and 
            self.datasets_cache and 
            (current_time - self.last_scan_time).seconds < 300):  # 5分钟缓存
            return self.datasets_cache
        
        datasets = {}
        dataset_id = 1
        
        try:
            if not os.path.exists(self.static_root):
                logger.warning(f"静态目录不存在: {self.static_root}")
                return datasets
            
            # 扫描static目录下的所有一级子目录
            for item in os.listdir(self.static_root):
                item_path = os.path.join(self.static_root, item)
                
                # 跳过非目录项和特殊目录
                if not os.path.isdir(item_path) or item.startswith('.') or item == 'img':
                    continue
                
                dataset_code = item
                dataset_info = self._analyze_dataset_folder(dataset_code, item_path, dataset_id)
                
                if dataset_info:
                    datasets[dataset_code] = dataset_info
                    dataset_id += 1
                    logger.info(f"发现数据集: {dataset_code} -> {dataset_info['name']}")
            
            # 特殊处理：如果只有img目录，创建默认数据集
            img_path = os.path.join(self.static_root, 'img')
            if os.path.exists(img_path) and os.path.isdir(img_path) and not datasets:
                default_dataset = self._analyze_dataset_folder('DEFAULT', img_path, 1)
                if default_dataset:
                    default_dataset['code'] = 'DEFAULT'
                    default_dataset['name'] = '默认数据集'
                    datasets['DEFAULT'] = default_dataset
                    logger.info("创建默认数据集")
            
        except Exception as e:
            logger.error(f"扫描数据集失败: {e}")
        
        # 更新缓存
        self.datasets_cache = datasets
        self.last_scan_time = current_time
        
        logger.info(f"数据集扫描完成，共发现 {len(datasets)} 个数据集")
        return datasets
    
    def _analyze_dataset_folder(self, code: str, folder_path: str, dataset_id: int) -> Optional[Dict]:
        """
        分析数据集文件夹，提取图片和元数据
        
        Args:
            code: 数据集代码
            folder_path: 文件夹路径
            dataset_id: 数据集ID
            
        Returns:
            Dict: 数据集信息
        """
        try:
            # 读取元数据文件（如果存在）
            metadata_path = os.path.join(folder_path, self.metadata_filename)
            metadata = {}
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    logger.warning(f"读取元数据文件失败 {metadata_path}: {e}")
            
            # 扫描图片文件
            images = []
            seq_counter = 1
            
            for filename in sorted(os.listdir(folder_path)):
                if filename == self.metadata_filename:
                    continue
                
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    # 检查是否为图片文件
                    _, ext = os.path.splitext(filename.lower())
                    if ext in self.image_extensions:
                        # 生成图片信息
                        image_info = {
                            'image_id': self._generate_image_id(dataset_id, seq_counter),
                            'dataset_id': dataset_id,
                            'filename': filename,
                            'seq_in_dataset': seq_counter,
                            'display_id': f"{code}-{seq_counter:04d}",
                            'file_size': os.path.getsize(file_path),
                            'created_at': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                        }
                        images.append(image_info)
                        seq_counter += 1
            
            if not images:
                logger.warning(f"数据集文件夹 {folder_path} 中未找到图片文件")
                return None
            
            # 构建数据集信息
            dataset_info = {
                'id': dataset_id,
                'code': code,
                'name': metadata.get('name', f'数据集 {code}'),
                'description': metadata.get('description', f'自动发现的数据集 {code}'),
                'category': metadata.get('category', 'general'),
                'created_at': metadata.get('created_at', datetime.now().isoformat()),
                'active': metadata.get('active', True),
                'folder_path': folder_path,
                'total_images': len(images),
                'images': images,
                'metadata': metadata
            }
            
            # 缓存图片信息
            for img in images:
                self.images_cache[img['image_id']] = img
            
            return dataset_info
            
        except Exception as e:
            logger.error(f"分析数据集文件夹失败 {folder_path}: {e}")
            return None
    
    def _generate_image_id(self, dataset_id: int, seq_in_dataset: int) -> int:
        """
        生成全局唯一的图片ID
        
        Args:
            dataset_id: 数据集ID
            seq_in_dataset: 数据集内序号
            
        Returns:
            int: 全局图片ID
        """
        # 使用简单的组合算法：dataset_id * 10000 + seq_in_dataset
        # 这样可以保证不同数据集的图片ID不冲突，同时保持一定的可读性
        return dataset_id * 10000 + seq_in_dataset
    
    def get_dataset_by_id(self, dataset_id: int) -> Optional[Dict]:
        """根据数据集ID获取数据集信息"""
        datasets = self.scan_datasets()
        for dataset in datasets.values():
            if dataset['id'] == dataset_id:
                return dataset
        return None
    
    def get_dataset_by_code(self, code: str) -> Optional[Dict]:
        """根据数据集代码获取数据集信息"""
        datasets = self.scan_datasets()
        return datasets.get(code)
    
    def get_image_by_id(self, image_id: int) -> Optional[Dict]:
        """根据图片ID获取图片信息"""
        # 确保缓存是最新的
        self.scan_datasets()
        return self.images_cache.get(image_id)
    
    def get_images_by_dataset(self, dataset_id: int) -> List[Dict]:
        """获取指定数据集的所有图片"""
        dataset = self.get_dataset_by_id(dataset_id)
        return dataset['images'] if dataset else []
    
    def create_dataset_metadata(self, code: str, metadata: Dict) -> bool:
        """
        为数据集创建元数据文件
        
        Args:
            code: 数据集代码
            metadata: 元数据字典
            
        Returns:
            bool: 是否创建成功
        """
        try:
            dataset_path = os.path.join(self.static_root, code)
            if not os.path.exists(dataset_path):
                os.makedirs(dataset_path, exist_ok=True)
            
            metadata_path = os.path.join(dataset_path, self.metadata_filename)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 强制刷新缓存
            self.scan_datasets(force_refresh=True)
            
            logger.info(f"创建数据集元数据成功: {code}")
            return True
            
        except Exception as e:
            logger.error(f"创建数据集元数据失败 {code}: {e}")
            return False
    
    def create_dataset_labels(self, dataset_id: int, labels: List[Dict]) -> bool:
        """
        为数据集创建标签
        
        Args:
            dataset_id: 数据集ID
            labels: 标签列表 [{"name": "正常", "description": ""}, ...]
            
        Returns:
            bool: 是否创建成功
        """
        try:
            from app.routes import db, LABELS  # 动态导入避免循环依赖
            
            created_labels = []
            for i, label_info in enumerate(labels):
                label_doc = {
                    "label_id": i + 1,
                    "dataset_id": dataset_id,
                    "name": label_info.get("name", f"标签{i+1}"),
                    "description": label_info.get("description", ""),
                    "active": True,
                    "created_at": datetime.now().isoformat()
                }
                
                # 保存到MongoDB
                try:
                    db.labels.insert_one(label_doc.copy())
                except Exception:
                    # MongoDB失败时保存到内存
                    pass
                
                # 保存到内存结构
                memory_label = {
                    "label_id": i + 1,
                    "dataset_id": dataset_id,
                    "name": label_info.get("name", f"标签{i+1}")
                }
                LABELS.append(memory_label)
                created_labels.append(memory_label)
            
            logger.info(f"为数据集 {dataset_id} 创建 {len(created_labels)} 个标签")
            return True
            
        except Exception as e:
            logger.error(f"创建数据集标签失败 {dataset_id}: {e}")
            return False
    
    def get_dataset_labels(self, dataset_id: int) -> List[Dict]:
        """获取数据集的标签列表"""
        try:
            from app.routes import db, LABELS
            
            # 优先从MongoDB获取
            try:
                labels = list(db.labels.find(
                    {"dataset_id": dataset_id, "active": {"$ne": False}}, 
                    {"_id": 0}
                ))
                if labels:
                    return sorted(labels, key=lambda x: x.get('label_id', 0))
            except Exception:
                pass
            
            # 备用内存数据
            memory_labels = [l for l in LABELS if l.get('dataset_id') == dataset_id]
            return sorted(memory_labels, key=lambda x: x.get('label_id', 0))
            
        except Exception as e:
            logger.error(f"获取数据集标签失败 {dataset_id}: {e}")
            return []
    
    def get_datasets_list(self) -> List[Dict]:
        """获取数据集列表（适用于API返回）"""
        datasets = self.scan_datasets()
        return [
            {
                'id': ds['id'],
                'code': ds['code'],
                'name': ds['name'],
                'description': ds['description'],
                'category': ds.get('category', 'general'),
                'total_images': ds['total_images'],
                'active': ds.get('active', True),
                'created_at': ds.get('created_at')
            }
            for ds in datasets.values()
            if ds.get('active', True)
        ]
    
    def get_export_data(self, dataset_id: Optional[int] = None) -> List[Dict]:
        """
        获取导出数据
        
        Args:
            dataset_id: 数据集ID，None表示导出所有数据集
            
        Returns:
            List[Dict]: 导出数据列表
        """
        from app.routes import db  # 动态导入避免循环依赖
        
        export_data = []
        datasets = self.scan_datasets()
        
        # 确定要导出的数据集
        target_datasets = []
        if dataset_id is None:
            target_datasets = list(datasets.values())
        else:
            target_dataset = self.get_dataset_by_id(dataset_id)
            if target_dataset:
                target_datasets = [target_dataset]
        
        # 获取标签信息
        labels_map = {}
        try:
            labels = list(db.labels.find({}, {'_id': 0}))
            for label in labels:
                key = (label['dataset_id'], label['label_id'])
                labels_map[key] = label['name']
        except:
            # 使用内存中的标签数据
            from app.routes import LABELS
            for label in LABELS:
                key = (label['dataset_id'], label['label_id'])
                labels_map[key] = label['name']
        
        # 导出每个数据集的数据
        for dataset in target_datasets:
            ds_id = dataset['id']
            
            # 获取该数据集的所有标注
            try:
                annotations = list(db.annotations.find({'dataset_id': ds_id}, {'_id': 0}))
            except:
                from app.routes import ANNOTATIONS
                annotations = [a for a in ANNOTATIONS if a['dataset_id'] == ds_id]
            
            # 为每张图片生成导出记录
            for image in dataset['images']:
                # 查找该图片的标注
                image_annotations = [a for a in annotations if a['image_id'] == image['image_id']]
                
                if image_annotations:
                    # 有标注的图片
                    for annotation in image_annotations:
                        label_key = (ds_id, annotation.get('label'))
                        export_record = {
                            'dataset_id': ds_id,
                            'dataset_code': dataset['code'],
                            'dataset_name': dataset['name'],
                            'image_id': image['image_id'],
                            'display_id': image['display_id'],
                            'seq_in_dataset': image['seq_in_dataset'],
                            'filename': image['filename'],
                            'label_id': annotation.get('label'),
                            'label_name': labels_map.get(label_key, '未知'),
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
                        'dataset_id': ds_id,
                        'dataset_code': dataset['code'],
                        'dataset_name': dataset['name'],
                        'image_id': image['image_id'],
                        'display_id': image['display_id'],
                        'seq_in_dataset': image['seq_in_dataset'],
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
        
        return export_data


# 全局数据集管理器实例
dataset_manager = DatasetManager()
