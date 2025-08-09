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
                # 注意：这里不再传递dataset_id，因为它会在_analyze_dataset_folder内部从元数据中读取
                dataset_info = self._analyze_dataset_folder(dataset_code, item_path)
                
                if dataset_info:
                    datasets[dataset_code] = dataset_info
                    logger.info(f"发现数据集: {dataset_code} -> {dataset_info['name']} (ID: {dataset_info['id']})")
            
            # 特殊处理：如果只有img目录，创建默认数据集
            img_path = os.path.join(self.static_root, 'img')
            if os.path.exists(img_path) and os.path.isdir(img_path) and not datasets:
                # 为默认数据集分配一个固定的高ID，避免与用户数据集冲突
                default_dataset = self._analyze_dataset_folder('DEFAULT', img_path, default_id=9999)
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
    
    def _analyze_dataset_folder(self, code: str, folder_path: str, default_id: int = None) -> Optional[Dict]:
        """
        分析数据集文件夹，提取图片和元数据。
        新逻辑：优先从元数据文件中读取固定的dataset_id，如果没有则生成新的唯一ID。
        """
        try:
            metadata_path = os.path.join(folder_path, self.metadata_filename)
            metadata = {}
            has_metadata = os.path.exists(metadata_path)

            if has_metadata:
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    logger.warning(f"读取元数据文件失败 {metadata_path}: {e}")
            
            # 获取或生成dataset_id
            dataset_id = None
            if 'dataset_id' in metadata:
                # 从元数据中读取已存储的ID
                dataset_id = metadata['dataset_id']
                logger.info(f"从元数据中读取数据集ID: {code} -> {dataset_id}")
            else:
                # 生成新的唯一ID
                if default_id is not None:
                    dataset_id = default_id
                else:
                    dataset_id = self._generate_unique_dataset_id()
                    logger.info(f"为数据集 {code} 生成新的唯一ID: {dataset_id}")
            
            # 扫描图片文件
            images = []
            seq_counter = 1
            
            for filename in sorted(os.listdir(folder_path)):
                if filename == self.metadata_filename:
                    continue
                
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(filename.lower())
                    if ext in self.image_extensions:
                        image_info = {
                            'image_id': self._generate_image_id(dataset_id, seq_counter),
                            'dataset_id': dataset_id,
                            'filename': filename,
                            'seq_in_dataset': seq_counter,
                            'display_id': f"{code}-{seq_counter:04d}",
                            'file_size': os.path.getsize(file_path),
                            'created_at': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                            'url': f"/static/{code}/{filename}"  # 添加完整的图片URL
                        }
                        images.append(image_info)
                        seq_counter += 1
            
            # 核心逻辑修改：如果存在元数据文件，即使没有图片，也视为有效数据集
            if not has_metadata and not images:
                logger.warning(f"跳过空目录且无元数据文件的文件夹: {folder_path}")
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
    
    def _generate_unique_dataset_id(self) -> int:
        """
        生成全局唯一的数据集ID
        
        Returns:
            int: 新的唯一数据集ID
        """
        # 扫描当前所有数据集，找到最大的ID
        max_id = 0
        try:
            # 检查当前缓存中的所有数据集
            for dataset in self.datasets_cache.values():
                if dataset.get('id', 0) > max_id:
                    max_id = dataset['id']
            
            # 还需要检查文件系统中所有的元数据文件，以防有些数据集还没加载到缓存
            if os.path.exists(self.static_root):
                for item in os.listdir(self.static_root):
                    item_path = os.path.join(self.static_root, item)
                    if os.path.isdir(item_path) and not item.startswith('.') and item != 'img':
                        metadata_path = os.path.join(item_path, self.metadata_filename)
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                    dataset_id = metadata.get('dataset_id', 0)
                                    if dataset_id > max_id:
                                        max_id = dataset_id
                            except:
                                pass
        except Exception as e:
            logger.warning(f"生成唯一ID时扫描失败: {e}")
        
        # 返回比当前最大ID大1的新ID，确保从合理的数字开始
        return max(max_id + 1, 1000)  # 最小从1000开始，避免与旧的测试数据冲突
    
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
        为数据集创建或更新元数据文件，并直接更新缓存。
        确保dataset_id被正确分配和持久化存储。
        
        Args:
            code: 数据集代码
            metadata: 元数据字典
            
        Returns:
            bool: 是否操作成功
        """
        try:
            dataset_path = os.path.join(self.static_root, code)
            if not os.path.exists(dataset_path):
                os.makedirs(dataset_path, exist_ok=True)
            
            # 确保metadata中包含唯一的dataset_id
            if 'dataset_id' not in metadata:
                # 如果缓存中已存在该数据集，使用其ID，否则分配新ID
                existing_dataset = self.datasets_cache.get(code)
                if existing_dataset:
                    metadata['dataset_id'] = existing_dataset['id']
                else:
                    metadata['dataset_id'] = self._generate_unique_dataset_id()
                logger.info(f"为数据集 {code} 分配ID: {metadata['dataset_id']}")
            
            metadata_path = os.path.join(dataset_path, self.metadata_filename)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # --- 优化：直接更新缓存，避免文件系统延迟 ---
            dataset_id = metadata['dataset_id']

            # 重新分析文件夹以获取最新信息（特别是图片列表）
            new_dataset_info = self._analyze_dataset_folder(code, dataset_path)

            # 将新信息或更新后的信息写入缓存
            if new_dataset_info:
                self.datasets_cache[code] = new_dataset_info
                logger.info(f"缓存已直接更新/创建: {code} (ID: {dataset_id})")
            else:
                # 如果分析失败，也尝试用基本信息更新缓存
                self.datasets_cache[code] = {
                    'id': dataset_id,
                    'code': code,
                    'name': metadata.get('name', f'数据集 {code}'),
                    'description': metadata.get('description', ''),
                    'folder_path': dataset_path,
                    'images': [],
                    'total_images': 0,
                    'metadata': metadata
                }
                logger.warning(f"分析文件夹失败，但仍使用基本信息更新了缓存: {code}")

            logger.info(f"创建/更新数据集元数据成功: {code}")
            return True
            
        except Exception as e:
            logger.error(f"创建/更新数据集元数据失败 {code}: {e}")
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
    
    def get_label_info(self, dataset_id: int, label_id: int) -> Optional[Dict]:
        """根据数据集ID和标签ID获取标签信息"""
        try:
            labels = self.get_dataset_labels(dataset_id)
            for label in labels:
                if label.get('label_id') == label_id:
                    return label
            return None
        except Exception as e:
            logger.error(f"获取标签信息失败 dataset_id={dataset_id}, label_id={label_id}: {e}")
            return None
    
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
