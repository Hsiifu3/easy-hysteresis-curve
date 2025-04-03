"""
可视化工具函数模块
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import logging

logger = logging.getLogger(__name__)

def set_chinese_font():
    """设置matplotlib中文字体"""
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        logger.info("成功设置中文字体")
    except Exception as e:
        logger.error(f"设置中文字体失败: {str(e)}")

def plot_hysteresis(ax, x, y, title="滞回曲线", xlabel="位移", ylabel="力", **kwargs):
    """绘制滞回曲线
    
    参数:
        ax: matplotlib轴对象
        x: x轴数据（位移）
        y: y轴数据（力）
        title: 图表标题
        xlabel: x轴标签
        ylabel: y轴标签
        **kwargs: 其他绘图参数
    """
    try:
        ax.plot(x, y, **kwargs)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True)
        ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
    except Exception as e:
        logger.error(f"绘制滞回曲线失败: {str(e)}")

def plot_peaks(ax, x, y, peaks, valleys, **kwargs):
    """在滞回曲线上标注峰谷值点
    
    参数:
        ax: matplotlib轴对象
        x: x轴数据
        y: y轴数据
        peaks: 峰值点索引
        valleys: 谷值点索引
        **kwargs: 其他绘图参数
    """
    try:
        ax.plot(x[peaks], y[peaks], "o", label="峰值", **kwargs)
        ax.plot(x[valleys], y[valleys], "s", label="谷值", **kwargs)
        ax.legend()
    except Exception as e:
        logger.error(f"标注峰谷值点失败: {str(e)}")

def plot_skeleton_curve(ax, envelope_points, **kwargs):
    """绘制骨架曲线
    
    参数:
        ax: matplotlib轴对象
        envelope_points: 包络线点集
        **kwargs: 其他绘图参数
    """
    try:
        x_env = [p[0] for p in envelope_points]
        y_env = [p[1] for p in envelope_points]
        ax.plot(x_env, y_env, '--', label="骨架曲线", **kwargs)
        ax.legend()
    except Exception as e:
        logger.error(f"绘制骨架曲线失败: {str(e)}")

def plot_stiffness_lines(ax, points, slopes, **kwargs):
    """绘制刚度线
    
    参数:
        ax: matplotlib轴对象
        points: 刚度线起点列表
        slopes: 对应的斜率列表
        **kwargs: 其他绘图参数
    """
    try:
        for point, slope in zip(points, slopes):
            x0, y0 = point
            x = np.array([x0-1, x0+1])
            y = slope * (x - x0) + y0
            ax.plot(x, y, ':', **kwargs)
    except Exception as e:
        logger.error(f"绘制刚度线失败: {str(e)}")