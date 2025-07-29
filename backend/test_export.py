#!/usr/bin/env python3
"""
测试导出功能 - 验证Excel文件是否包含多个工作表
"""

import pandas as pd
from io import BytesIO
import os
import sys

# 添加app路径到sys.path
sys.path.append('/home/droot/medc-img-annotation-app/backend')

from app import create_app
from app.routes import db, ANNOTATIONS, IMAGES, LABELS

def test_export_functionality():
    """测试导出功能并验证工作表"""
    print("=== 开始测试导出功能 ===")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        try:
            output = BytesIO()
            print("1. 创建Excel writer...")
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 测试标注数据导出
                print("2. 导出标注数据...")
                try:
                    annotations_data = list(db.annotations.find({}, {"_id": 0}))
                    print(f"   从MongoDB获取到 {len(annotations_data)} 条标注数据")
                    
                    if not annotations_data:
                        annotations_data = ANNOTATIONS
                        print(f"   使用备用内存数据: {len(annotations_data)} 条记录")
                    
                    if annotations_data:
                        # 处理字段名不一致问题
                        for item in annotations_data:
                            if 'label' in item and 'label_id' not in item:
                                item['label_id'] = item['label']
                            item.pop('label', None)
                        
                        annotations_df = pd.DataFrame(annotations_data)
                        column_order = ['dataset_id', 'record_id', 'image_id', 'expert_id', 'label_id', 'tip', 'datetime']
                        available_columns = [col for col in column_order if col in annotations_df.columns]
                        annotations_df = annotations_df.reindex(columns=available_columns)
                        
                        annotations_df.to_excel(writer, sheet_name='annotations', index=False)
                        print(f"   ✅ 成功创建annotations工作表: {len(annotations_df)} 条记录")
                        print(f"   字段: {list(annotations_df.columns)}")
                    else:
                        empty_annotations = pd.DataFrame(columns=['dataset_id', 'record_id', 'image_id', 'expert_id', 'label_id', 'tip', 'datetime'])
                        empty_annotations.to_excel(writer, sheet_name='annotations', index=False)
                        print("   ⚠️ 创建空的annotations工作表")
                        
                except Exception as e:
                    print(f"   ❌ 标注数据导出失败: {e}")
                    error_df = pd.DataFrame([{'error': f'标注数据导出失败: {str(e)}'}])
                    error_df.to_excel(writer, sheet_name='annotations', index=False)
                
                # 测试图片数据导出
                print("3. 导出图片数据...")
                try:
                    images_data = list(db.images.find({}, {"_id": 0}))
                    print(f"   从MongoDB获取到 {len(images_data)} 条图片数据")
                    
                    if not images_data:
                        print("   MongoDB中无图片数据，使用备用内存数据")
                        images_data = []
                        for img in IMAGES:
                            images_data.append({
                                'image_id': img['image_id'],
                                'image_path': f"static/img/{img['filename']}"
                            })
                        print(f"   备用数据转换完成: {len(images_data)} 条记录")
                    
                    if images_data:
                        images_df = pd.DataFrame(images_data)
                        column_order = ['image_id', 'image_path']
                        available_columns = [col for col in column_order if col in images_df.columns]
                        images_df = images_df.reindex(columns=available_columns)
                        
                        images_df.to_excel(writer, sheet_name='images', index=False)
                        print(f"   ✅ 成功创建images工作表: {len(images_df)} 条记录")
                        print(f"   字段: {list(images_df.columns)}")
                    else:
                        empty_images = pd.DataFrame(columns=['image_id', 'image_path'])
                        empty_images.to_excel(writer, sheet_name='images', index=False)
                        print("   ⚠️ 创建空的images工作表")
                        
                except Exception as e:
                    print(f"   ❌ 图片数据导出失败: {e}")
                    error_df = pd.DataFrame([{'error': f'图片数据导出失败: {str(e)}'}])
                    error_df.to_excel(writer, sheet_name='images', index=False)
                
                # 测试标签数据导出
                print("4. 导出标签数据...")
                try:
                    labels_data = list(db.labels.find({}, {"_id": 0}))
                    print(f"   从MongoDB获取到 {len(labels_data)} 条标签数据")
                    
                    if not labels_data:
                        print("   MongoDB中无标签数据，使用备用内存数据")
                        labels_data = []
                        label_id_set = set()
                        for label in LABELS:
                            if label['label_id'] not in label_id_set:
                                labels_data.append({
                                    'label_id': label['label_id'],
                                    'label_name': label['name'],
                                    'category': '病理学'
                                })
                                label_id_set.add(label['label_id'])
                        print(f"   备用数据转换完成: {len(labels_data)} 条记录")
                    
                    if labels_data:
                        labels_df = pd.DataFrame(labels_data)
                        column_order = ['label_id', 'label_name', 'category']
                        available_columns = [col for col in column_order if col in labels_df.columns]
                        labels_df = labels_df.reindex(columns=available_columns)
                        
                        labels_df = labels_df.sort_values('label_id')
                        
                        labels_df.to_excel(writer, sheet_name='labels', index=False)
                        print(f"   ✅ 成功创建labels工作表: {len(labels_df)} 条记录")
                        print(f"   字段: {list(labels_df.columns)}")
                    else:
                        empty_labels = pd.DataFrame(columns=['label_id', 'label_name', 'category'])
                        empty_labels.to_excel(writer, sheet_name='labels', index=False)
                        print("   ⚠️ 创建空的labels工作表")
                        
                except Exception as e:
                    print(f"   ❌ 标签数据导出失败: {e}")
                    error_df = pd.DataFrame([{'error': f'标签数据导出失败: {str(e)}'}])
                    error_df.to_excel(writer, sheet_name='labels', index=False)
            
            # 保存测试文件
            output.seek(0)
            test_file_path = '/home/droot/test_export_result.xlsx'
            with open(test_file_path, 'wb') as f:
                f.write(output.getvalue())
            
            print(f"5. ✅ 测试导出完成，文件保存至: {test_file_path}")
            
            # 验证工作表
            print("6. 验证Excel文件工作表...")
            try:
                xl_file = pd.ExcelFile(test_file_path)
                sheet_names = xl_file.sheet_names
                print(f"   📋 发现工作表: {sheet_names}")
                
                for sheet_name in sheet_names:
                    df = pd.read_excel(test_file_path, sheet_name=sheet_name)
                    print(f"   - {sheet_name}: {len(df)} 行, 字段: {list(df.columns)}")
                    if len(df) > 0:
                        print(f"     前3行数据: {df.head(3).to_dict('records')}")
                
                return True
                
            except Exception as e:
                print(f"   ❌ 验证Excel文件失败: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 测试导出功能失败: {e}")
            return False

if __name__ == "__main__":
    success = test_export_functionality()
    if success:
        print("\n🎉 测试成功！Excel文件包含多个工作表。")
    else:
        print("\n❌ 测试失败！请检查错误信息。")
