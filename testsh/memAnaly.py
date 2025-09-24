import psutil
import time
import json
from datetime import datetime

class ResourceMonitor:
    def __init__(self):
        self.data = []
    
    def analyze_image_processing_memory(self):
        """分析图像处理的内存需求（不含AI模型）"""
        # 医学图像标注的实际场景
        scenarios = {
            "DICOM图像加载": {
                "file_size_mb": 50,  # 典型CT/MRI切片
                "processing_multiplier": 3,  # 图像解码和缓存
                "concurrent_users": 8  # 8个医生同时标注
            },
            "多层图像序列": {
                "file_size_mb": 200,  # 多层序列文件
                "processing_multiplier": 2.5,  # 序列加载和渲染
                "concurrent_users": 5
            },
            "标注数据处理": {
                "annotation_data_mb": 20,  # 标注坐标、形状数据
                "image_overlay_mb": 30,    # 叠加层渲染
                "concurrent_users": 10
            },
            "图像缩放渲染": {
                "base_image_mb": 50,
                "zoom_levels": 4,  # 4个缩放级别缓存
                "concurrent_users": 8
            }
        }
        
        total_memory_needed = 0
        
        print("=== 医学图像标注系统内存需求分析 ===")
        for scenario, config in scenarios.items():
            if "annotation_data_mb" in config:
                # 标注数据处理场景
                memory_per_user = config["annotation_data_mb"] + config["image_overlay_mb"]
            elif "zoom_levels" in config:
                # 图像缩放场景
                memory_per_user = config["base_image_mb"] * config["zoom_levels"]
            else:
                # 标准图像处理场景
                memory_per_user = config["file_size_mb"] * config["processing_multiplier"]
            
            total_scenario_memory = memory_per_user * config["concurrent_users"]
            total_memory_needed += total_scenario_memory
            
            print(f"{scenario}:")
            print(f"  单用户内存需求: {memory_per_user}MB")
            print(f"  并发用户数: {config['concurrent_users']}")
            print(f"  场景总内存: {total_scenario_memory}MB")
            print()
        
        # 加上系统开销和Web服务内存
        web_service_memory = 512  # Flask + 数据库连接池等
        system_overhead = total_memory_needed * 0.4  # 40%系统开销（医学应用稳定性要求高）
        recommended_memory = (total_memory_needed + system_overhead + web_service_memory) / 1024
        
        print(f"应用总内存需求: {total_memory_needed}MB")
        print(f"Web服务内存: {web_service_memory}MB")
        print(f"系统开销(40%): {system_overhead}MB")
        print(f"推荐内存配置: {recommended_memory:.1f}GB")
        
        return recommended_memory

    def analyze_concurrent_doctor_usage(self):
        """分析医生并发使用模式"""
        # 基于实际医院工作模式
        usage_patterns = {
            "上午诊断高峰": {
                "time_period": "9:00-12:00",
                "concurrent_doctors": 8,
                "avg_session_duration_min": 45,
                "images_per_session": 15
            },
            "下午复查时段": {
                "time_period": "14:00-17:00", 
                "concurrent_doctors": 6,
                "avg_session_duration_min": 30,
                "images_per_session": 10
            },
            "晚间紧急会诊": {
                "time_period": "19:00-22:00",
                "concurrent_doctors": 3,
                "avg_session_duration_min": 60,
                "images_per_session": 20
            }
        }
        
        print("\n=== 医生使用模式分析 ===")
        max_concurrent = 0
        peak_memory_mb = 0
        
        for pattern, data in usage_patterns.items():
            concurrent = data["concurrent_doctors"]
            max_concurrent = max(max_concurrent, concurrent)
            
            # 每个医生的内存使用估算
            memory_per_doctor = (
                50 * 3 +  # 当前查看的图像
                20 +       # 标注数据
                30 +       # UI缓存
                50         # 浏览器渲染缓存
            )  # 150MB per doctor
            
            pattern_memory = memory_per_doctor * concurrent
            peak_memory_mb = max(peak_memory_mb, pattern_memory)
            
            print(f"{pattern} ({data['time_period']}):")
            print(f"  并发医生: {concurrent}人")
            print(f"  单医生内存: {memory_per_doctor}MB")
            print(f"  时段峰值内存: {pattern_memory}MB")
            print(f"  平均会话时长: {data['avg_session_duration_min']}分钟")
            print()
        
        print(f"系统峰值并发: {max_concurrent}人")
        print(f"峰值内存需求: {peak_memory_mb}MB ({peak_memory_mb/1024:.1f}GB)")
        
        return max_concurrent, peak_memory_mb

    def calculate_cpu_requirements(self, max_concurrent_doctors):
        """计算CPU需求"""
        # 医学图像处理的CPU密集操作
        cpu_intensive_operations = {
            "DICOM解析": {"cpu_percent_per_user": 8, "duration_sec": 3},
            "图像格式转换": {"cpu_percent_per_user": 15, "duration_sec": 2},
            "标注渲染": {"cpu_percent_per_user": 5, "duration_sec": 1},
            "数据库查询": {"cpu_percent_per_user": 3, "duration_sec": 0.5},
            "并发响应处理": {"cpu_percent_per_user": 10, "duration_sec": 0.2}
        }
        
        print("\n=== CPU需求分析 ===")
        total_cpu_percent = 0
        
        for operation, specs in cpu_intensive_operations.items():
            cpu_per_user = specs["cpu_percent_per_user"]
            total_operation_cpu = cpu_per_user * max_concurrent_doctors
            total_cpu_percent += total_operation_cpu
            
            print(f"{operation}:")
            print(f"  单用户CPU: {cpu_per_user}%")
            print(f"  {max_concurrent_doctors}并发CPU: {total_operation_cpu}%")
        
        # 计算所需CPU核心数（保持70%利用率）
        target_utilization = 70
        required_cores = max(4, int((total_cpu_percent / target_utilization) + 0.5))
        
        print(f"\n总CPU需求: {total_cpu_percent}%")
        print(f"目标利用率: {target_utilization}%")
        print(f"推荐CPU核心数: {required_cores}核")
        
        return required_cores

    def generate_recommendations(self, memory_gb, cpu_cores, max_concurrent):
        """生成最终配置推荐"""
        return {
            "当前演示环境": {
                "cpu_cores": 2,
                "memory_gb": 2,
                "concurrent_users": 2,
                "适用场景": "功能演示、验收测试",
                "限制": ["并发用户少", "可能出现卡顿", "不适合生产使用"]
            },
            "生产环境推荐": {
                "cpu_cores": cpu_cores,
                "memory_gb": memory_gb,
                "concurrent_users": max_concurrent,
                "适用场景": "正式医院部署",
                "优势": ["支持8-10医生并发", "响应速度快", "系统稳定可靠"]
            },
            "配置对比": {
                "性能提升": f"CPU性能提升{cpu_cores/2:.1f}倍",
                "内存提升": f"内存容量提升{memory_gb/2:.1f}倍", 
                "并发提升": f"并发能力提升{max_concurrent/2:.1f}倍"
            }
        }

    def save_detailed_report(self):
        """生成详细的配置需求报告"""
        memory_gb = self.analyze_image_processing_memory()
        max_concurrent, peak_memory_mb = self.analyze_concurrent_doctor_usage()
        cpu_cores = self.calculate_cpu_requirements(max_concurrent)
        
        # 取较大值确保充足
        final_memory_gb = max(memory_gb, peak_memory_mb/1024 * 1.3)  # 30%安全边际
        final_cpu_cores = max(cpu_cores, 4)  # 最少4核
        
        recommendations = self.generate_recommendations(int(final_memory_gb), final_cpu_cores, max_concurrent)
        
        report = {
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "项目": "医学图像标注系统",
            "分析结果": {
                "理论内存需求": f"{memory_gb:.1f}GB",
                "实际内存需求": f"{final_memory_gb:.1f}GB", 
                "CPU核心需求": f"{final_cpu_cores}核",
                "最大并发医生": f"{max_concurrent}人"
            },
            "配置推荐": recommendations,
            "成本效益分析": {
                "演示环境成本": "约300元/月",
                "生产环境成本": "约1000元/月",
                "成本差异原因": "生产环境需要更高配置保证医疗系统稳定性和响应速度"
            }
        }
        
        with open('医学图像标注系统配置需求报告.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印总结
        print("\n" + "="*50)
        print("📊 配置需求总结")
        print("="*50)
        print(f"演示环境: 2核2GB (当前) ✅")
        print(f"生产环境: {final_cpu_cores}核{int(final_memory_gb)}GB (推荐) 🎯")
        print(f"主要原因:")
        print(f"  • 支持{max_concurrent}医生同时标注")
        print(f"  • 医学图像文件大(50-200MB)")
        print(f"  • 图像处理内存放大3倍")
        print(f"  • 医疗系统稳定性要求高")
        print("="*50)
        
        return report

if __name__ == "__main__":
    monitor = ResourceMonitor()
    report = monitor.save_detailed_report()
    print(f"\n📄 详细报告已保存: 医学图像标注系统配置需求报告.json")