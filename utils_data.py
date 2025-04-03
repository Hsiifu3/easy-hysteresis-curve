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

# ==================== 循环识别与分析函数 ====================

def identify_cycles_by_direction(displacement, force, cycle_count=3, min_prominence=0.05, start_threshold=0.05):
    """
    通过位移和力的变化方向识别加载循环
    
    参数:
        displacement (array): 位移数据数组
        force (array): 力数据数组
        cycle_count (int): 期望识别的循环数量
        min_prominence (float): 峰值识别的最小突出度（相对于数据范围的比例）
        start_threshold (float): 起始阈值，用于忽略接近原点的初始点（相对于最大位移幅值的比例）
        
    返回:
        tuple: (cycles, cycle_features, error)
            - cycles: 字典，键为循环编号，值为(displacement, force)元组
            - cycle_features: 字典，包含每个循环的特征信息
            - error: 错误信息，如果没有错误则为None
    """
    try:
        if len(displacement) != len(force):
            return {}, {}, "位移和力数据长度不匹配"
            
        if len(displacement) < 10:
            return {}, {}, "数据点太少，无法识别循环"
            
        # 计算起始阈值（绝对值）
        disp_max = np.max(np.abs(displacement))
        abs_start_threshold = disp_max * start_threshold
        
        # 平滑数据，减少噪声影响
        window_size = min(15, len(displacement) // 10)
        if window_size % 2 == 0:
            window_size += 1  # 确保窗口大小为奇数
            
        disp_smoothed = savgol_filter(displacement, window_size, 3)
        force_smoothed = savgol_filter(force, window_size, 3)
        
        # 计算位移和力的归一化值，用于增强峰值检测
        disp_range = np.max(disp_smoothed) - np.min(disp_smoothed)
        force_range = np.max(force_smoothed) - np.min(force_smoothed)
        
        if disp_range == 0 or force_range == 0:
            return {}, {}, "位移或力范围为零，无法识别循环"
            
        disp_norm = (disp_smoothed - np.min(disp_smoothed)) / disp_range
        force_norm = (force_smoothed - np.min(force_smoothed)) / force_range
        
        # 综合指标 = 位移归一化值 + 力归一化值
        combined_signal = disp_norm + force_norm
        
        # 计算位移和力的变化率
        disp_derivative = np.gradient(disp_smoothed)
        force_derivative = np.gradient(force_smoothed)
        
        # 设置峰值检测的最小突出度（相对于数据范围的比例）
        abs_min_prominence = min_prominence * (np.max(combined_signal) - np.min(combined_signal))
        
        # 检测峰值点和谷值点（在综合指标上）
        peaks, _ = find_peaks(combined_signal, prominence=abs_min_prominence)
        valleys, _ = find_peaks(-combined_signal, prominence=abs_min_prominence)
        
        # 调试输出
        print(f"检测到 {len(peaks)} 个峰值点和 {len(valleys)} 个谷值点")
        
        # 筛除接近原点的初始点（位移幅值小于阈值的点）
        filtered_peaks = []
        for peak in peaks:
            if abs(displacement[peak]) > abs_start_threshold:  # 只保留位移幅值大于阈值的点
                filtered_peaks.append(peak)
                
        filtered_valleys = []
        for valley in valleys:
            if abs(displacement[valley]) > abs_start_threshold:  # 只保留位移幅值大于阈值的点
                filtered_valleys.append(valley)
                
        print(f"过滤起始阶段后剩余 {len(filtered_peaks)} 个峰值点和 {len(filtered_valleys)} 个谷值点")
        
        # 如果过滤后的峰谷点过少，调整突出度重新尝试
        if len(filtered_peaks) < cycle_count or len(filtered_valleys) < cycle_count:
            adjusted_min_prominence = min_prominence * 0.5  # 降低突出度要求
            abs_adjusted_prominence = adjusted_min_prominence * (np.max(combined_signal) - np.min(combined_signal))
            
            peaks, _ = find_peaks(combined_signal, prominence=abs_adjusted_prominence)
            valleys, _ = find_peaks(-combined_signal, prominence=abs_adjusted_prominence)
            
            # 重新过滤接近原点的点
            filtered_peaks = [p for p in peaks if abs(displacement[p]) > abs_start_threshold]
            filtered_valleys = [v for v in valleys if abs(displacement[v]) > abs_start_threshold]
            
            print(f"调整突出度后检测到 {len(filtered_peaks)} 个峰值点和 {len(filtered_valleys)} 个谷值点")
        
        # 评分机制：根据位移和力的变化幅度，给每个峰、谷点打分
        peak_scores = []
        for peak in filtered_peaks:
            # 计算该点的位移和力相对于均值的偏差
            disp_dev = abs(displacement[peak] - np.mean(displacement))
            force_dev = abs(force[peak] - np.mean(force))
            
            # 归一化偏差
            norm_disp_dev = disp_dev / (np.max(displacement) - np.min(displacement)) if np.max(displacement) != np.min(displacement) else 0
            norm_force_dev = force_dev / (np.max(force) - np.min(force)) if np.max(force) != np.min(force) else 0
            
            # 综合得分 (加权和)
            score = 0.6 * norm_disp_dev + 0.4 * norm_force_dev
            peak_scores.append((peak, score))
        
        valley_scores = []
        for valley in filtered_valleys:
            disp_dev = abs(displacement[valley] - np.mean(displacement))
            force_dev = abs(force[valley] - np.mean(force))
            
            norm_disp_dev = disp_dev / (np.max(displacement) - np.min(displacement)) if np.max(displacement) != np.min(displacement) else 0
            norm_force_dev = force_dev / (np.max(force) - np.min(force)) if np.max(force) != np.min(force) else 0
            
            score = 0.6 * norm_disp_dev + 0.4 * norm_force_dev
            valley_scores.append((valley, score))
        
        # 按得分排序并取得分最高的前N个点
        peak_scores.sort(key=lambda x: x[1], reverse=True)
        valley_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 根据指定的循环数选择对应数量的峰谷点
        selected_peaks = [p[0] for p in peak_scores[:cycle_count]] if len(peak_scores) >= cycle_count else [p[0] for p in peak_scores]
        selected_valleys = [v[0] for v in valley_scores[:cycle_count]] if len(valley_scores) >= cycle_count else [v[0] for v in valley_scores]
        
        # 按索引排序
        selected_peaks.sort()
        selected_valleys.sort()
        
        print(f"最终选择 {len(selected_peaks)} 个峰值点和 {len(selected_valleys)} 个谷值点")
        
        # 调试可视化
        try:
            # 创建调试输出目录
            debug_dir = "debug_output"
            os.makedirs(debug_dir, exist_ok=True)
            
            # 1. 显示原始峰值检测结果
            plt.figure(figsize=(12, 8))
            plt.subplot(2, 1, 1)
            plt.plot(displacement, label='位移')
            plt.plot(peaks, displacement[peaks], "rx", markersize=10, label='峰值')
            plt.plot(valleys, displacement[valleys], "gx", markersize=10, label='谷值')
            plt.legend()
            plt.title("位移数据峰谷检测")
            plt.axhline(y=abs_start_threshold, color='b', linestyle='--', alpha=0.5, label=f'起始阈值 ({start_threshold:.2f})')
            plt.axhline(y=-abs_start_threshold, color='b', linestyle='--', alpha=0.5)
            
            plt.subplot(2, 1, 2)
            plt.plot(force, label='力')
            plt.plot(peaks, force[peaks], "rx", markersize=10, label='峰值')
            plt.plot(valleys, force[valleys], "gx", markersize=10, label='谷值')
            plt.legend()
            plt.title("力数据峰谷检测")
            
            plt.tight_layout()
            plt.savefig(os.path.join(debug_dir, "peak_detection_original.png"))
            plt.close()
            
            # 2. 显示综合指标信号和峰谷点
            plt.figure(figsize=(12, 6))
            plt.plot(combined_signal, label='综合指标')
            plt.plot(peaks, combined_signal[peaks], "rx", markersize=10, label='峰值')
            plt.plot(valleys, combined_signal[valleys], "gx", markersize=10, label='谷值')
            plt.title("综合指标峰谷检测")
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(debug_dir, "combined_signal_detection.png"))
            plt.close()
            
            # 3. 显示过滤后的峰谷点
            plt.figure(figsize=(12, 8))
            plt.subplot(2, 1, 1)
            plt.plot(displacement, label='位移')
            plt.plot(filtered_peaks, displacement[filtered_peaks], "rx", markersize=10, label='过滤后峰值')
            plt.plot(filtered_valleys, displacement[filtered_valleys], "gx", markersize=10, label='过滤后谷值')
            plt.legend()
            plt.title("过滤后位移数据峰谷检测")
            plt.axhline(y=abs_start_threshold, color='b', linestyle='--', alpha=0.5, label=f'起始阈值 ({start_threshold:.2f})')
            plt.axhline(y=-abs_start_threshold, color='b', linestyle='--', alpha=0.5)
            
            plt.subplot(2, 1, 2)
            plt.plot(force, label='力')
            plt.plot(filtered_peaks, force[filtered_peaks], "rx", markersize=10, label='过滤后峰值')
            plt.plot(filtered_valleys, force[filtered_valleys], "gx", markersize=10, label='过滤后谷值')
            plt.legend()
            plt.title("过滤后力数据峰谷检测")
            
            plt.tight_layout()
            plt.savefig(os.path.join(debug_dir, "peak_detection_filtered.png"))
            plt.close()
            
            # 4. 显示最终选择的峰谷点
            plt.figure(figsize=(12, 8))
            plt.subplot(2, 1, 1)
            plt.plot(displacement, label='位移')
            plt.plot(selected_peaks, displacement[selected_peaks], "ro", markersize=10, label='选择的峰值')
            plt.plot(selected_valleys, displacement[selected_valleys], "go", markersize=10, label='选择的谷值')
            plt.legend()
            plt.title("最终选择的峰谷点 (位移)")
            
            plt.subplot(2, 1, 2)
            plt.plot(force, label='力')
            plt.plot(selected_peaks, force[selected_peaks], "ro", markersize=10, label='选择的峰值')
            plt.plot(selected_valleys, force[selected_valleys], "go", markersize=10, label='选择的谷值')
            plt.legend()
            plt.title("最终选择的峰谷点 (力)")
            
            plt.tight_layout()
            plt.savefig(os.path.join(debug_dir, "peak_detection_final.png"))
            plt.close()
            
        except Exception as e:
            print(f"调试可视化出错: {str(e)}")
        
        # 将峰值点和谷值点组合，并确保它们按正确的顺序排列
        extreme_points = []
        
        # 根据得分最高的点判断第一个极值点类型
        first_type = 'peak' if (selected_peaks and selected_valleys and 
                              selected_peaks[0] < selected_valleys[0]) else 'valley'
                              
        # 初始化循环
        cycles = {}
        cycle_features = {}
        
        # 对循环进行编号，从1开始
        cycle_num = 1
        
        # 如果点数量不足，返回错误
        if len(selected_peaks) == 0 or len(selected_valleys) == 0:
            return {}, {}, f"识别的峰谷点不足，无法形成完整循环。检测到 {len(selected_peaks)} 个峰值点和 {len(selected_valleys)} 个谷值点。"
            
        # 确保峰值点和谷值点的数量大致相同
        min_points = min(len(selected_peaks), len(selected_valleys))
        selected_peaks = selected_peaks[:min_points]
        selected_valleys = selected_valleys[:min_points]
        
        # 组织循环数据
        for i in range(min_points):
            peak_idx = selected_peaks[i]
            
            if i < len(selected_valleys):
                valley_idx = selected_valleys[i]
                
                # 根据索引顺序确定循环的起止点
                if peak_idx < valley_idx:
                    start_idx, end_idx = peak_idx, valley_idx
                    peak_first = True
                else:
                    start_idx, end_idx = valley_idx, peak_idx
                    peak_first = False
                    
                # 提取这段数据
                if end_idx + 1 < len(displacement):
                    cycle_disp = displacement[start_idx:end_idx+1]
                    cycle_force = force[start_idx:end_idx+1]
                else:
                    cycle_disp = displacement[start_idx:end_idx]
                    cycle_force = force[start_idx:end_idx]
                    
                # 存储数据
                if len(cycle_disp) > 5:  # 确保有足够的点形成循环
                    cycles[cycle_num] = (cycle_disp, cycle_force)
                    
                    # 记录特征点
                    if peak_first:
                        positive_peak = (displacement[peak_idx], force[peak_idx])
                        negative_peak = (displacement[valley_idx], force[valley_idx])
                    else:
                        positive_peak = (displacement[valley_idx], force[valley_idx])
                        negative_peak = (displacement[peak_idx], force[peak_idx])
                        
                    cycle_features[cycle_num] = {
                        'positive_peak': positive_peak,
                        'negative_peak': negative_peak,
                        'peak_idx': peak_idx,
                        'valley_idx': valley_idx
                    }
                    
                    cycle_num += 1
                    
        if not cycles:
            return {}, {}, "无法识别有效循环"
            
        print(f"成功识别 {len(cycles)} 个循环")
        return cycles, cycle_features, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {}, {}, f"循环识别过程出错: {str(e)}"