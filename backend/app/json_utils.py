"""
JSON序列化工具 - 处理MongoDB ObjectId序列化问题
"""
import json
from datetime import datetime
from bson import ObjectId


class JSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理MongoDB ObjectId和datetime对象"""
    
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def to_json(data):
    """
    将包含ObjectId的数据转换为JSON字符串
    
    Args:
        data: 要序列化的数据
        
    Returns:
        str: JSON字符串
    """
    return json.dumps(data, cls=JSONEncoder, ensure_ascii=False)


def convert_objectid_to_str(data):
    """
    递归地将数据中的ObjectId转换为字符串
    
    Args:
        data: 待转换的数据（可以是dict, list或其他类型）
        
    Returns:
        转换后的数据
    """
    if isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


def safe_jsonify(data):
    """
    安全地将数据转换为可JSON序列化的格式
    主要用于Flask的jsonify函数之前的数据预处理
    
    Args:
        data: 待处理的数据
        
    Returns:
        可安全序列化的数据
    """
    return convert_objectid_to_str(data)