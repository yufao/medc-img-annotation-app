import os
import time
import threading
import queue
from pymongo import MongoClient
import json
from datetime import datetime
import traceback
from typing import List, Dict, Any, Callable, Optional
import multiprocessing
from PIL import Image
import hashlib

# 导入日志模块
from utils.logger import logger

class BatchImporter:
    """数据集批量导入工具
    
    支持大型数据集的分批导入，具有以下特性：
    - 多线程/多进程支持
    - 进度跟踪
    - 错误处理与重试
    - 支持暂停/恢复
    """
    
    def __init__(self, db_client, batch_size=100, max_workers=None, use_multiprocessing=False):
        """初始化批量导入工具
        
        Args:
            db_client: MongoDB客户端
            batch_size: 每批处理的图像数量
            max_workers: 最大工作线程/进程数，默认为CPU核心数的2倍
            use_multiprocessing: 是否使用多进程而非多线程
        """
        self.db_client = db_client
        self.batch_size = batch_size
        self.max_workers = max_workers or min(multiprocessing.cpu_count() * 2, 8)  # 限制最大工作数
        self.use_multiprocessing = use_multiprocessing
        
        # 进度追踪
        self.total_items = 0
        self.processed_items = 0
        self.successful_items = 0
        self.failed_items = 0
        self.progress_callback = None
        
        # 任务队列
        self.task_queue = queue.Queue() if not use_multiprocessing else multiprocessing.Queue()
        
        # 导入状态
        self.import_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.end_time = None
        
        # 错误记录
        self.errors = []
        
        # 锁，用于线程安全的操作共享资源
        self.lock = threading.Lock() if not use_multiprocessing else multiprocessing.Lock()
    
    def import_dataset(self, dataset_path: str, 
                      dataset_name: str,
                      label_file: Optional[str] = None,
                      progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """导入数据集
        
        Args:
            dataset_path: 数据集图像目录路径
            dataset_name: 数据集名称
            label_file: 标签文件路径，JSON或CSV格式
            progress_callback: 进度回调函数，接收进度百分比和状态信息
            
        Returns:
            包含导入结果的字典
        """
        # 重置状态
        self._reset_state()
        self.progress_callback = progress_callback
        
        try:
            # 1. 扫描目录，获取所有图像文件
            logger.info(f"开始扫描数据集: {dataset_path}")
            image_files = self._scan_directory(dataset_path)
            self.total_items = len(image_files)
            
            if self.total_items == 0:
                logger.warning(f"数据集目录 {dataset_path} 中未找到支持的图像文件")
                return {"success": False, "message": "未找到图像文件", "stats": self._get_stats()}
            
            logger.info(f"找到 {self.total_items} 个图像文件")
            
            # 2. 加载标签（如果有）
            labels = {}
            if label_file and os.path.exists(label_file):
                logger.info(f"加载标签文件: {label_file}")
                labels = self._load_labels(label_file)
                logger.info(f"成功加载 {len(labels)} 条标签")
            
            # 3. 创建数据集记录
            dataset_doc = {
                "name": dataset_name,
                "path": dataset_path,
                "import_id": self.import_id,
                "created_at": datetime.utcnow(),
                "total_images": self.total_items,
                "import_status": "importing"
            }
            
            # 插入数据集记录
            datasets_collection = self.db_client.medcimgdb.datasets
            dataset_result = datasets_collection.insert_one(dataset_doc)
            dataset_id = dataset_result.inserted_id
            
            # 4. 将任务添加到队列
            for i, img_path in enumerate(image_files):
                file_name = os.path.basename(img_path)
                file_label = labels.get(file_name, {})
                
                self.task_queue.put({
                    "index": i,
                    "image_path": img_path,
                    "file_name": file_name,
                    "labels": file_label,
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name
                })
            
            # 5. 启动工作线程/进程
            self.is_running = True
            self.start_time = time.time()
            workers = []
            
            logger.info(f"启动 {self.max_workers} 个工作{'进程' if self.use_multiprocessing else '线程'}")
            
            for i in range(self.max_workers):
                if self.use_multiprocessing:
                    worker = multiprocessing.Process(target=self._worker_process, args=(i,))
                else:
                    worker = threading.Thread(target=self._worker_process, args=(i,))
                worker.daemon = True
                worker.start()
                workers.append(worker)
            
            # 6. 等待所有工作完成
            for worker in workers:
                worker.join()
            
            self.end_time = time.time()
            self.is_running = False
            
            # 7. 更新数据集状态
            datasets_collection.update_one(
                {"_id": dataset_id},
                {
                    "$set": {
                        "import_status": "completed",
                        "successful_images": self.successful_items,
                        "failed_images": self.failed_items,
                        "completed_at": datetime.utcnow(),
                        "duration_seconds": self.end_time - self.start_time
                    }
                }
            )
            
            # 8. 返回结果
            duration = self.end_time - self.start_time
            success_rate = (self.successful_items / self.total_items) * 100 if self.total_items > 0 else 0
            
            logger.info(f"数据集导入完成。总计: {self.total_items}, 成功: {self.successful_items}, "
                       f"失败: {self.failed_items}, 耗时: {duration:.2f}秒, 成功率: {success_rate:.2f}%")
            
            return {
                "success": True,
                "message": "数据集导入完成",
                "dataset_id": str(dataset_id),
                "stats": self._get_stats()
            }
            
        except Exception as e:
            logger.error(f"数据集导入失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "message": f"导入过程出错: {str(e)}",
                "stats": self._get_stats()
            }
    
    def pause(self):
        """暂停导入过程"""
        self.is_paused = True
        logger.info("导入过程已暂停")
    
    def resume(self):
        """恢复导入过程"""
        self.is_paused = False
        logger.info("导入过程已恢复")
    
    def stop(self):
        """停止导入过程"""
        self.is_running = False
        logger.info("导入过程已停止")
    
    def _reset_state(self):
        """重置状态"""
        self.total_items = 0
        self.processed_items = 0
        self.successful_items = 0
        self.failed_items = 0
        self.errors = []
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.end_time = None
        
        # 清空队列
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except queue.Empty:
                break
    
    def _get_stats(self) -> Dict[str, Any]:
        """获取导入统计信息"""
        duration = 0
        if self.start_time:
            end = self.end_time or time.time()
            duration = end - self.start_time
        
        return {
            "import_id": self.import_id,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "duration_seconds": duration,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "errors": self.errors[:100],  # 最多返回100个错误
            "progress_percent": (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0
        }
    
    def _scan_directory(self, dir_path: str) -> List[str]:
        """扫描目录，返回所有支持的图像文件路径"""
        supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.dcm', '.nii', '.nii.gz'}
        image_files = []
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_extensions:
                    image_files.append(os.path.join(root, file))
        
        return image_files
    
    def _load_labels(self, label_file: str) -> Dict[str, Any]:
        """加载标签文件，支持JSON和CSV格式"""
        ext = os.path.splitext(label_file)[1].lower()
        
        if ext == '.json':
            with open(label_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif ext == '.csv':
            import csv
            labels = {}
            with open(label_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 假设CSV文件有filename和label列
                    if 'filename' in row:
                        labels[row['filename']] = {k: v for k, v in row.items() if k != 'filename'}
            return labels
        else:
            logger.warning(f"不支持的标签文件格式: {ext}")
            return {}
    
    def _worker_process(self, worker_id: int):
        """工作线程/进程处理函数"""
        logger.info(f"工作{'进程' if self.use_multiprocessing else '线程'} {worker_id} 已启动")
        
        while self.is_running:
            # 如果暂停，等待
            if self.is_paused:
                time.sleep(0.5)
                continue
            
            try:
                # 获取任务，设置超时以便检查是否应该停止
                try:
                    task = self.task_queue.get(timeout=0.5)
                except queue.Empty:
                    # 队列为空，检查是否所有任务都已处理
                    with self.lock:
                        if self.processed_items >= self.total_items:
                            break
                    continue
                
                # 处理图像导入
                success = self._process_image(task, worker_id)
                
                # 更新进度
                with self.lock:
                    self.processed_items += 1
                    if success:
                        self.successful_items += 1
                    else:
                        self.failed_items += 1
                    
                    # 调用进度回调
                    if self.progress_callback and callable(self.progress_callback):
                        progress_percent = (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0
                        self.progress_callback(progress_percent, self._get_stats())
                
            except Exception as e:
                logger.error(f"工作{'进程' if self.use_multiprocessing else '线程'} {worker_id} 异常: {str(e)}")
                logger.error(traceback.format_exc())
        
        logger.info(f"工作{'进程' if self.use_multiprocessing else '线程'} {worker_id} 已退出")
    
    def _process_image(self, task: Dict[str, Any], worker_id: int) -> bool:
        """处理单个图像导入
        
        Args:
            task: 包含图像信息的任务字典
            worker_id: 工作线程/进程ID
            
        Returns:
            导入是否成功
        """
        try:
            image_path = task['image_path']
            file_name = task['file_name']
            labels = task.get('labels', {})
            dataset_id = task['dataset_id']
            dataset_name = task['dataset_name']
            
            # 1. 读取图像文件并获取基本信息
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    format_name = img.format
                    mode = img.mode
            except Exception as e:
                logger.error(f"无法读取图像 {file_name}: {str(e)}")
                with self.lock:
                    self.errors.append({
                        "file": file_name,
                        "error": f"图像读取失败: {str(e)}",
                        "time": datetime.now().isoformat()
                    })
                return False
            
            # 2. 计算文件hash作为唯一标识
            file_hash = self._calculate_file_hash(image_path)
            
            # 3. 检查是否已存在
            images_collection = self.db_client.medcimgdb.images
            existing = images_collection.find_one({"file_hash": file_hash})
            if existing:
                logger.info(f"图像 {file_name} 已存在，跳过导入")
                return True
            
            # 4. 创建图像文档
            image_doc = {
                "filename": file_name,
                "file_path": image_path,
                "file_hash": file_hash,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "width": width,
                "height": height,
                "format": format_name,
                "mode": mode,
                "file_size": os.path.getsize(image_path),
                "labels": labels,
                "annotations": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "import_id": self.import_id
            }
            
            # 5. 插入到数据库
            images_collection.insert_one(image_doc)
            
            logger.debug(f"成功导入图像: {file_name}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"处理图像 {task.get('file_name', 'unknown')} 失败: {error_msg}")
            
            with self.lock:
                self.errors.append({
                    "file": task.get('file_name', 'unknown'),
                    "error": error_msg,
                    "time": datetime.now().isoformat()
                })
            
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
