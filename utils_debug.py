"""
调试工具模块

提供用于调试和日志记录的工具函数
"""

import logging
import os
import json
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):
    """用于JSON序列化numpy数组的编码器"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def save_debug_data(data, filename, debug_dir="debug_output"):
    """保存调试数据到JSON文件
    
    参数:
        data: 要保存的数据字典
        filename: 文件名
        debug_dir: 调试输出目录
    """
    try:
        # 创建调试输出目录
        os.makedirs(debug_dir, exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = os.path.join(debug_dir, f"{filename}_{timestamp}.json")
        
        # 保存数据
        with open(full_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=NumpyEncoder, indent=2, ensure_ascii=False)
        
        logger.info(f"调试数据已保存到: {full_filename}")
        
    except Exception as e:
        logger.error(f"保存调试数据失败: {str(e)}")

def load_debug_data(filepath):
    """从JSON文件加载调试数据
    
    参数:
        filepath: JSON文件路径
    
    返回:
        加载的数据字典
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 将列表转换回numpy数组
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = np.array(value)
        
        logger.info(f"已从{filepath}加载调试数据")
        return data
    
    except Exception as e:
        logger.error(f"加载调试数据失败: {str(e)}")
        return None

def plot_debug_data(data, save_dir="debug_output"):
    """绘制调试数据的图表
    
    参数:
        data: 调试数据字典
        save_dir: 图表保存目录
    """
    try:
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 为每个数据创建单独的图表
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                plt.figure(figsize=(10, 6))
                if value.ndim == 1:
                    plt.plot(value)
                elif value.ndim == 2:
                    plt.plot(value[:, 0], value[:, 1])
                
                plt.title(key)
                plt.grid(True)
                
                # 保存图表
                plt.savefig(os.path.join(save_dir, f"debug_plot_{key}_{timestamp}.png"))
                plt.close()
        
        logger.info(f"调试图表已保存到: {save_dir}")
        
    except Exception as e:
        logger.error(f"绘制调试图表失败: {str(e)}")

def print_array_info(arr, name="array"):
    """打印数组的基本信息
    
    参数:
        arr: numpy数组
        name: 数组名称
    """
    try:
        print(f"\n{name} 信息:")
        print(f"形状: {arr.shape}")
        print(f"类型: {arr.dtype}")
        print(f"最小值: {np.min(arr)}")
        print(f"最大值: {np.max(arr)}")
        print(f"均值: {np.mean(arr)}")
        print(f"标准差: {np.std(arr)}")
        
    except Exception as e:
        logger.error(f"打印数组信息失败: {str(e)}")

def memory_usage_info():
    """获取当前进程的内存使用信息"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        print("\n内存使用信息:")
        print(f"RSS (常驻集大小): {mem_info.rss / 1024 / 1024:.2f} MB")
        print(f"VMS (虚拟内存大小): {mem_info.vms / 1024 / 1024:.2f} MB")
        
    except ImportError:
        logger.warning("未安装psutil模块，无法获取内存使用信息")
    except Exception as e:
        logger.error(f"获取内存使用信息失败: {str(e)}")

def time_function(func):
    """函数执行时间装饰器
    
    参数:
        func: 要计时的函数
    """
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"函数 {func.__name__} 执行时间: {duration:.3f} 秒")
        return result
    return wrapper