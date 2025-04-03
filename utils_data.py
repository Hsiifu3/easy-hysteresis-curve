"""
准静态试验数据处理工具模块

该模块提供了一系列函数用于处理准静态试验数据，包括：
- 数据读取与预处理
- 循环加载识别
- 滞回曲线分析
- 等效刚度计算
- 能量耗散计算
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, savgol_filter
import os
from scipy.ndimage import uniform_filter1d
import logging

logger = logging.getLogger(__name__)

def calculate_stiffness(displacement, force):
    """计算等效刚度
    
    使用最大位移点和最小位移点之间的割线计算等效刚度
    (F_max - F_min)/(Δ_max - Δ_min)
    
    参数:
        displacement (ndarray): 位移数据
        force (ndarray): 力数据
        
    返回:
        tuple: (stiffness, error_message)
    """
    try:
        # 确保数据为数值类型并且不包含无穷大或NaN
        displacement = np.nan_to_num(displacement, nan=0.0, posinf=0.0, neginf=0.0)
        force = np.nan_to_num(force, nan=0.0, posinf=0.0, neginf=0.0)
        
        if len(displacement) < 2:
            return 0, "数据点不足"
            
        # 只保留有限值
        valid_indices = np.isfinite(displacement) & np.isfinite(force)
        disp_valid = displacement[valid_indices]
        force_valid = force[valid_indices]
        
        if len(disp_valid) < 2:
            return 0, "有效数据点不足"
        
        # 查找最大和最小位移点
        max_disp_idx = np.argmax(disp_valid)
        min_disp_idx = np.argmin(disp_valid)
        
        # 获取对应的位移和力值
        max_disp = disp_valid[max_disp_idx]
        min_disp = disp_valid[min_disp_idx]
        max_disp_force = force_valid[max_disp_idx]
        min_disp_force = force_valid[min_disp_idx]
        
        # 计算位移差和力差
        disp_diff = max_disp - min_disp
        force_diff = max_disp_force - min_disp_force
        
        # 计算割线刚度: (F_max - F_min)/(Δ_max - Δ_min)
        if abs(disp_diff) > 1e-10:  # 避免除以接近零的数
            stiffness = force_diff / disp_diff
            return stiffness, None
        else:
            # 如果位移差太小，使用线性拟合
            slope, _ = np.polyfit(disp_valid, force_valid, 1)
            return slope, "位移差过小，使用线性拟合计算刚度"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return 0, f"刚度计算错误: {str(e)}"

def calculate_equivalent_stiffness(cycles, cycle_features):
    """计算等效刚度
    
    参数:
        cycles (dict): 循环数据字典
        cycle_features (dict): 循环特征字典
        
    返回:
        tuple: (cycle_stiffness_dict, avg_stiffness, cumulative_stiffness, error_message)
    """
    try:
        cycle_stiffness = {}
        cycle_stiffness_values = []
        
        for cycle_num, (cycle_disp, cycle_force) in cycles.items():
            # 获取特征点信息
            features = cycle_features.get(cycle_num, {})
            anomaly = features.get('anomaly', False)
            
            # 记录刚度信息
            if cycle_num not in cycle_stiffness:
                cycle_stiffness[cycle_num] = {}
                
            # 使用正向峰值点和负向峰值点计算等效刚度
            if 'positive_peak' in features and features['positive_peak'] is not None and \
               'negative_peak' in features and features['negative_peak'] is not None:
                # 提取正向峰值点和负向峰值点
                pos_peak = features['positive_peak']  # (disp, force)
                neg_peak = features['negative_peak']  # (disp, force)
                
                # 计算等效刚度 (F_max - F_min) / (Disp_max - Disp_min)
                disp_diff = pos_peak[0] - neg_peak[0]
                force_diff = pos_peak[1] - neg_peak[1]
                
                if abs(disp_diff) > 1e-10:  # 避免除以接近零的数
                    peak_stiffness = force_diff / disp_diff
                else:
                    peak_stiffness = 0
                    
                # 保存峰值点计算的等效刚度结果
                cycle_stiffness[cycle_num] = {
                    'equivalent': peak_stiffness,
                    'max_disp': pos_peak[0],
                    'min_disp': neg_peak[0],
                    'max_disp_force': pos_peak[1],
                    'min_disp_force': neg_peak[1],
                    'anomaly': anomaly
                }
                
                # 只有非异常值才计入平均
                if not anomaly and peak_stiffness != 0:
                    cycle_stiffness_values.append(peak_stiffness)
            else:
                # 如果没有峰值点信息，回退到使用最大和最小位移点的方法
                # 查找最大和最小位移点
                max_disp_idx = np.argmax(cycle_disp)
                min_disp_idx = np.argmin(cycle_disp)
                
                # 计算等效刚度
                disp_diff = cycle_disp[max_disp_idx] - cycle_disp[min_disp_idx]
                force_diff = cycle_force[max_disp_idx] - cycle_force[min_disp_idx]
                
                if abs(disp_diff) > 1e-10:
                    fallback_stiffness = force_diff / disp_diff
                else:
                    fallback_stiffness = 0
                
                # 记录结果
                cycle_stiffness[cycle_num] = {
                    'equivalent': fallback_stiffness,
                    'max_disp': cycle_disp[max_disp_idx],
                    'min_disp': cycle_disp[min_disp_idx],
                    'max_disp_force': cycle_force[max_disp_idx],
                    'min_disp_force': cycle_force[min_disp_idx],
                    'anomaly': anomaly,
                    'note': '使用最大最小位移点计算（无峰值点）'
                }
                
                # 只有非异常值才计入平均
                if not anomaly and fallback_stiffness != 0:
                    cycle_stiffness_values.append(fallback_stiffness)
        
        # 计算平均刚度
        avg_stiffness = np.mean(cycle_stiffness_values) if cycle_stiffness_values else 0
        
        # 计算累积刚度退化（每3个循环计算移动平均值）
        cumulative_stiffness = []
        if len(cycle_stiffness_values) >= 3:
            window_size = 3
            for i in range(len(cycle_stiffness_values) - window_size + 1):
                window_avg = np.mean(cycle_stiffness_values[i:i+window_size])
                cumulative_stiffness.append((i+window_size, window_avg))
        
        return cycle_stiffness, avg_stiffness, cumulative_stiffness, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {}, 0, [], f"等效刚度计算错误: {str(e)}"

def generate_skeleton_curve_improved(cycles, cycle_features):
    """从特征点生成骨架曲线
    
    参数:
        cycles (dict): 循环数据字典
        cycle_features (dict): 循环特征字典
        
    返回:
        tuple: (skeleton_disp, skeleton_force, error_message)
    """
    try:
        skeleton_points = []
        positive_points = []  # 正峰值点列表
        negative_points = []  # 负峰值点列表
        
        # 按照循环顺序分离正负峰值点
        for cycle_num, features in sorted(cycle_features.items()):
            # 添加正向峰值点
            if 'positive_peak' in features and features['positive_peak'] is not None:
                if not features.get('anomaly', False):  # 排除标记为异常的点
                    positive_points.append(features['positive_peak'])
            
            # 添加负向峰值点
            if 'negative_peak' in features and features['negative_peak'] is not None:
                if not features.get('anomaly', False):  # 排除标记为异常的点
                    negative_points.append(features['negative_peak'])
        
        # 添加原点作为起始点
        origin_point = (0.0, 0.0)
        skeleton_points.append(origin_point)
        
        # 按照位移值从小到大排序负峰值点和正峰值点
        negative_points.sort(key=lambda p: p[0])
        positive_points.sort(key=lambda p: p[0])
        
        # 添加所有负峰值点（从小到大）
        for point in negative_points:
            # 使用3位小数精度判断是否已存在相似点
            rounded_point = (round(point[0], 3), round(point[1], 3))
            existing_rounded = [(round(p[0], 3), round(p[1], 3)) for p in skeleton_points]
            if rounded_point not in existing_rounded:
                skeleton_points.append(point)
        
        # 添加所有正峰值点（从小到大）
        for point in positive_points:
            # 使用3位小数精度判断是否已存在相似点
            rounded_point = (round(point[0], 3), round(point[1], 3))
            existing_rounded = [(round(p[0], 3), round(p[1], 3)) for p in skeleton_points]
            if rounded_point not in existing_rounded:
                skeleton_points.append(point)
                
        # 按照位移大小排序确保曲线平滑
        skeleton_points.sort(key=lambda x: x[0])
        
        # 检查是否有足够的点生成骨架曲线
        if len(skeleton_points) >= 2:
            skeleton_disp, skeleton_force = zip(*skeleton_points)
            return np.array(skeleton_disp), np.array(skeleton_force), None
        else:
            return np.array([]), np.array([]), "点数不足，无法生成有效的骨架曲线"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return np.array([]), np.array([]), f"骨架曲线生成出错: {str(e)}"

def identify_cycles(displacement, force, cycle_count, prominence=0.1):
    """识别循环加载圈数
    
    参数:
        displacement (ndarray): 位移数据
        force (ndarray): 力数据
        cycle_count (int): 期望识别的循环数
        prominence (float): 峰值识别的阈值(0-1)，值越大识别的峰越显著
        
    返回:
        tuple: (cycles_dict, error_message)
    """
    try:
        # 替换可能的无穷大值和NaN值
        displacement = np.nan_to_num(displacement, nan=0.0, posinf=0.0, neginf=0.0)
        force = np.nan_to_num(force, nan=0.0, posinf=0.0, neginf=0.0)
        
        # 确保数据非空且有效
        if len(displacement) < 10:
            return {}, "数据点数量过少，无法识别循环"
        
        # 数据预处理 - 去除NaN值
        valid_indices = np.isfinite(displacement) & np.isfinite(force)
        displacement = displacement[valid_indices]
        force = force[valid_indices]
        
        if len(displacement) == 0:
            return {}, "有效数据点为空，请检查数据"
        
        # 计算数据范围用于归一化
        disp_range = np.max(displacement) - np.min(displacement)
        force_range = np.max(force) - np.min(force)
        
        if disp_range == 0 or force_range == 0:
            return {}, "位移或力数据范围为零，无法识别循环"
        
        # 尝试通过位移数据识别循环
        abs_max = np.max(np.abs(displacement))
        if abs_max == 0:
            return {}, "位移数据全为零，无法识别循环"
        
        # 根据prominence参数调整峰值识别的灵敏度
        prominence_val = prominence * abs_max
        peaks, _ = find_peaks(displacement, prominence=prominence_val)
        valleys, _ = find_peaks(-displacement, prominence=prominence_val)
        
        # 合并并排序所有的关键点
        all_points = np.sort(np.concatenate([peaks, valleys]))
        
        # 如果没有检测到足够的峰谷点，尝试使用等分方法
        if len(all_points) < cycle_count + 1:
            # 如果没有足够的峰谷点，尝试直接等分数据
            print(f"未检测到足够的峰谷点，使用等分法识别循环。已检测到点数: {len(all_points)}")
            
            # 使用等分法
            step = len(displacement) // (cycle_count + 1)
            all_points = np.array([i * step for i in range(cycle_count + 1)])
            all_points[-1] = min(all_points[-1], len(displacement) - 1)  # 确保最后一个点不超出范围
        
        # 构建循环字典
        cycles = {}
        
        # 取最小值使得不会超出检测到的峰谷点数量
        points_count = min(cycle_count, len(all_points) - 1)
        
        for i in range(points_count):
            start_idx = all_points[i]
            end_idx = all_points[i+1]
            
            # 确保分段有足够的点
            if end_idx - start_idx > 5:  # 至少需要6个点才能形成有意义的循环
                cycle_disp = displacement[start_idx:end_idx]
                cycle_force = force[start_idx:end_idx]
                cycles[i+1] = (cycle_disp, cycle_force)
        
        # 如果没有找到有效循环，尝试简单地将数据分成请求的循环数
        if not cycles and len(displacement) > cycle_count * 10:
            segment_size = len(displacement) // cycle_count
            for i in range(cycle_count):
                start_idx = i * segment_size
                end_idx = (i + 1) * segment_size if i < cycle_count - 1 else len(displacement)
                
                cycle_disp = displacement[start_idx:end_idx]
                cycle_force = force[start_idx:end_idx]
                cycles[i+1] = (cycle_disp, cycle_force)
            
            print(f"使用数据分段法识别到 {len(cycles)} 个循环")
        
        # 如果仍然没有找到有效循环
        if not cycles:
            return {}, "无法识别有效的循环，请调整参数后重试"
        
        return cycles, None
    except Exception as e:
        return {}, f"循环识别过程中出错: {str(e)}"

def generate_skeleton_curve(cycle_data):
    """生成骨架曲线"""
    try:
        if not cycle_data:
            return np.array([]), np.array([]), "没有循环数据"
            
        skeleton_points = []
        
        for cycle_num, (cycle_disp, cycle_force) in cycle_data.items():
            # 确保数据有效
            if len(cycle_disp) < 2:
                continue
                
            # 找出力的最大和最小点
            max_idx = np.argmax(cycle_force)
            min_idx = np.argmin(cycle_force)
            
            # 添加到骨架曲线点集
            skeleton_points.append((cycle_disp[max_idx], cycle_force[max_idx]))
            skeleton_points.append((cycle_disp[min_idx], cycle_force[min_idx]))
        
        # 按位移排序
        if skeleton_points:
            skeleton_points.sort(key=lambda x: x[0])
            skeleton_disp, skeleton_force = zip(*skeleton_points)
            return np.array(skeleton_disp), np.array(skeleton_force), None
        else:
            return np.array([]), np.array([]), "无法生成骨架曲线点"
    except Exception as e:
        return np.array([]), np.array([]), f"骨架曲线生成出错: {str(e)}"

def convert_units(value, from_unit, to_unit):
    """单位转换功能"""
    # 位移单位转换 (基准:mm)
    displacement_factors = {
        "mm": 1.0,
        "cm": 10.0,
        "m": 1000.0,
        "in": 25.4,
        "ft": 304.8
    }
    
    # 力单位转换 (基准:kN)
    force_factors = {
        "N": 0.001,
        "kN": 1.0,
        "MN": 1000.0,
        "lbf": 0.004448,
        "kip": 4.448
    }
    
    # 确定使用哪个转换因子
    if from_unit in displacement_factors and to_unit in displacement_factors:
        from_factor = displacement_factors[from_unit]
        to_factor = displacement_factors[to_unit]
        # 从源单位转到mm再转到目标单位
        return value * (from_factor / to_factor)
    
    elif from_unit in force_factors and to_unit in force_factors:
        from_factor = force_factors[from_unit]
        to_factor = force_factors[to_unit]
        # 从源单位转到kN再转到目标单位
        return value * (from_factor / to_factor)
    
    else:
        # 不支持的单位
        return value

def debug_plot_data(displacement, force, title="原始数据"):
    """调试函数：绘制原始数据"""
    plt.figure(figsize=(10, 6))
    plt.plot(displacement, force, 'b.-')
    plt.title(title)
    plt.xlabel("位移")
    plt.ylabel("力")
    plt.grid(True)
    plt.tight_layout()
    return plt.gcf()

def debug_plot_cycles(cycles, title="循环识别结果"):
    """调试函数：绘制识别的循环"""
    plt.figure(figsize=(10, 6))
    for cycle_num, (disp, force) in cycles.items():
        plt.plot(disp, force, label=f"循环 {cycle_num}")
    plt.title(title)
    plt.xlabel("位移")
    plt.ylabel("力")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    return plt.gcf()

def debug_plot_skeleton_with_cycles(displacement, force, skeleton_disp, skeleton_force, cycles=None, title="骨架曲线"):
    """调试函数：同时显示原始数据、循环和骨架曲线"""
    plt.figure(figsize=(10, 6))
    
    # 绘制原始数据
    plt.plot(displacement, force, 'b-', alpha=0.3, label="原始数据")
    
    # 绘制循环
    if cycles:
        colors = plt.cm.tab10.colors
        for i, (cycle_num, (cycle_disp, cycle_force)) in enumerate(cycles.items()):
            color_idx = i % len(colors)
            plt.plot(cycle_disp, cycle_force, '--', color=colors[color_idx], alpha=0.7, label=f"循环 {cycle_num}")
    
    # 绘制骨架曲线
    plt.plot(skeleton_disp, skeleton_force, 'ro-', linewidth=2, markersize=6, label="骨架曲线")
    
    plt.title(title)
    plt.xlabel("位移")
    plt.ylabel("力")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    return plt.gcf()

def debug_plot_stiffness_degradation(cumulative_stiffness, title="刚度退化曲线"):
    """调试函数：绘制刚度退化曲线"""
    if not cumulative_stiffness:
        return None
        
    plt.figure(figsize=(10, 6))
    cycles, stiffness = zip(*cumulative_stiffness)
    plt.plot(cycles, stiffness, 'bo-', linewidth=2)
    plt.title(title)
    plt.xlabel("循环数")
    plt.ylabel("累积等效刚度")
    plt.grid(True)
    plt.tight_layout()
    return plt.gcf()

# ==================== 能量耗散与滞回特性函数 ====================

def calculate_energy_dissipation(displacement, force):
    # 实现计算能量耗散的逻辑
    pass

# ==================== 其他辅助计算函数 ====================

def unit_conversion(value, from_unit, to_unit):
    # 实现单位转换的逻辑
    pass