"""
准静态试验分析工具 - 可视化模块

该模块包含所有图表绘制和结果可视化功能
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import utils_visualization as uv
import logging

logger = logging.getLogger(__name__)

class HysteresisViz:
    """滞回曲线可视化类"""
    
    def __init__(self, figure, canvas, result_text):
        """初始化可视化管理器
        
        参数:
            figure: Matplotlib图形对象
            canvas: Matplotlib画布
            result_text: 结果文本组件
        """
        self.fig = figure
        self.canvas = canvas
        self.result_text = result_text
        self.current_disp_unit = "mm"
        self.current_force_unit = "kN"
    
    def set_units(self, disp_unit, force_unit):
        """设置单位
        
        参数:
            disp_unit: 位移单位
            force_unit: 力单位
        """
        self.current_disp_unit = disp_unit
        self.current_force_unit = force_unit
    
    def update_result(self, text):
        """更新结果文本
        
        参数:
            text: 要添加的文本
        """
        self.result_text.insert("end", text)
        self.result_text.see("end")
    
    def clear_result(self):
        """清空结果文本"""
        self.result_text.delete(1.0, "end")
    
    def draw_raw_hysteresis(self, displacement, force, disp_unit="mm", force_unit="kN"):
        """绘制原始滞回曲线
        
        参数:
            displacement: 位移数据
            force: 力数据
            disp_unit: 位移单位
            force_unit: 力单位
        """
        try:
            # 更新单位
            self.current_disp_unit = disp_unit
            self.current_force_unit = force_unit
            
            # 清空图形
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            
            # 绘制滞回曲线
            ax.plot(displacement, force, 'b-')
            
            # 设置标签和标题
            ax.set_xlabel(f"位移 ({self.current_disp_unit})")
            ax.set_ylabel(f"力 ({self.current_force_unit})")
            ax.set_title("原始滞回曲线")
            
            # 添加网格和原点参考线
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
            
            # 重新绘制
            self.fig.tight_layout()
            self.canvas.draw()
            
            # 更新结果区域
            self.clear_result()
            self.update_result("原始滞回曲线\n\n")
            self.update_result(f"数据点数: {len(displacement)}\n")
            self.update_result(f"位移范围: [{min(displacement):.3f} ~ {max(displacement):.3f}] {self.current_disp_unit}\n")
            self.update_result(f"力范围: [{min(force):.3f} ~ {max(force):.3f}] {self.current_force_unit}\n")
            
            return True
        
        except Exception as e:
            logger.error(f"绘制原始滞回曲线出错: {str(e)}")
            self.clear_result()
            self.update_result(f"绘制滞回曲线出错: {str(e)}\n")
            return False
    
    def draw_processed_hysteresis_with_cycles(self, displacement, force, cycles, peaks, valleys, disp_unit="mm", force_unit="kN"):
        """绘制处理后的滞回曲线和识别的循环
        
        参数:
            displacement: 位移数据
            force: 力数据
            cycles: 循环起止索引列表
            peaks: 峰值点索引
            valleys: 谷值点索引
            disp_unit: 位移单位
            force_unit: 力单位
        """
        try:
            # 更新单位
            self.current_disp_unit = disp_unit
            self.current_force_unit = force_unit
            
            # 清空图形
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            
            # 绘制处理后的滞回曲线
            ax.plot(displacement, force, 'b-', alpha=0.5, label="完整数据")
            
            # 绘制峰谷值点
            if peaks is not None and len(peaks) > 0:
                ax.plot(displacement[peaks], force[peaks], 'ro', label="峰值点")
            if valleys is not None and len(valleys) > 0:
                ax.plot(displacement[valleys], force[valleys], 'go', label="谷值点")
            
            # 绘制各个循环
            colors = plt.cm.tab10.colors
            for i, (start_idx, end_idx) in enumerate(cycles):
                cycle_idx = i % len(colors)
                cycle_disp = displacement[start_idx:end_idx]
                cycle_force = force[start_idx:end_idx]
                ax.plot(cycle_disp, cycle_force, '-', color=colors[cycle_idx], linewidth=2,
                       label=f"循环 {i+1}")
            
            # 设置标签和标题
            ax.set_xlabel(f"位移 ({self.current_disp_unit})")
            ax.set_ylabel(f"力 ({self.current_force_unit})")
            ax.set_title("处理后滞回曲线及循环识别")
            
            # 添加网格和原点参考线
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
            
            # 添加图例
            ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0)
            
            # 重新绘制
            self.fig.tight_layout()
            self.canvas.draw()
            
            # 更新结果区域
            self.clear_result()
            self.update_result("处理后滞回曲线及循环识别\n\n")
            self.update_result(f"数据点数: {len(displacement)}\n")
            self.update_result(f"识别循环数: {len(cycles)}\n")
            self.update_result(f"峰值点数: {len(peaks) if peaks is not None else 0}\n")
            self.update_result(f"谷值点数: {len(valleys) if valleys is not None else 0}\n\n")
            
            for i, (start_idx, end_idx) in enumerate(cycles):
                cycle_disp = displacement[start_idx:end_idx]
                cycle_force = force[start_idx:end_idx]
                self.update_result(f"循环 {i+1}:\n")
                self.update_result(f"  点数: {len(cycle_disp)}\n")
                self.update_result(f"  位移范围: [{min(cycle_disp):.3f} ~ {max(cycle_disp):.3f}] {self.current_disp_unit}\n")
                self.update_result(f"  力范围: [{min(cycle_force):.3f} ~ {max(cycle_force):.3f}] {self.current_force_unit}\n\n")
            
            return True
        
        except Exception as e:
            logger.error(f"绘制处理后滞回曲线出错: {str(e)}")
            self.clear_result()
            self.update_result(f"绘制处理后滞回曲线出错: {str(e)}\n")
            return False
    
    def show_equivalent_stiffness_results(self, results, disp_unit="mm", force_unit="kN"):
        """显示等效刚度计算结果
        
        参数:
            results: 等效刚度计算结果字典
            disp_unit: 位移单位
            force_unit: 力单位
        """
        try:
            # 更新单位
            self.current_disp_unit = disp_unit
            self.current_force_unit = force_unit
            
            # 清空结果区域
            self.clear_result()
            self.update_result("等效刚度计算结果\n\n")
            
            # 显示每个循环的等效刚度
            self.update_result(f"{'循环':<6}{'位移范围 ('+disp_unit+')':<20}{'力范围 ('+force_unit+')':<20}{'等效刚度 ('+force_unit+'/'+disp_unit+')':<20}{'能量耗散':<15}\n")
            self.update_result("-" * 80 + "\n")
            
            # 计算平均刚度
            total_stiffness = 0
            valid_cycle_count = 0
            
            for cycle_idx, result in results.items():
                stiffness = result["stiffness"]
                energy = result["energy_dissipation"]
                max_disp = result["max_disp"]
                min_disp = result["min_disp"]
                max_force = result["max_force"]
                min_force = result["min_force"]
                disp_range = max_disp - min_disp
                force_range = max_force - min_force
                
                self.update_result(f"{cycle_idx+1:<6}{min_disp:.3f} ~ {max_disp:.3f}  {min_force:.3f} ~ {max_force:.3f}  {stiffness:.3f}  {energy:.3f}\n")
                
                total_stiffness += stiffness
                valid_cycle_count += 1
            
            # 显示平均刚度
            if valid_cycle_count > 0:
                avg_stiffness = total_stiffness / valid_cycle_count
                self.update_result("-" * 80 + "\n")
                self.update_result(f"平均等效刚度: {avg_stiffness:.3f} {force_unit}/{disp_unit}\n")
            
            return True
        
        except Exception as e:
            logger.error(f"显示等效刚度计算结果出错: {str(e)}")
            self.clear_result()
            self.update_result(f"显示等效刚度计算结果出错: {str(e)}\n")
            return False
    
    def draw_cycles_with_stiffness(self, displacement, force, cycles, stiffness_results, disp_unit="mm", force_unit="kN"):
        """绘制循环滞回曲线和等效刚度线
        
        参数:
            displacement: 位移数据
            force: 力数据
            cycles: 循环起止索引列表
            stiffness_results: 等效刚度计算结果
            disp_unit: 位移单位
            force_unit: 力单位
        """
        try:
            # 更新单位
            self.current_disp_unit = disp_unit
            self.current_force_unit = force_unit
            
            # 清空图形
            self.fig.clear()
            
            # 创建两个子图
            ax1 = self.fig.add_subplot(211)  # 上半部分 - 循环和刚度线
            ax2 = self.fig.add_subplot(212)  # 下半部分 - 刚度变化
            
            # 绘制循环和刚度线
            colors = plt.cm.tab10.colors
            
            # 首先绘制完整数据的轮廓
            ax1.plot(displacement, force, 'k-', alpha=0.2)
            
            # 计算平均刚度
            total_stiffness = 0
            stiffness_values = []
            cycle_indices = []
            
            for i, (start_idx, end_idx) in enumerate(cycles):
                cycle_idx = i % len(colors)
                cycle_disp = displacement[start_idx:end_idx]
                cycle_force = force[start_idx:end_idx]
                
                # 获取该循环的等效刚度
                if i in stiffness_results:
                    stiffness = stiffness_results[i]["stiffness"]
                    total_stiffness += stiffness
                    stiffness_values.append(stiffness)
                    cycle_indices.append(i+1)
                    
                    # 绘制循环曲线
                    ax1.plot(cycle_disp, cycle_force, '-', color=colors[cycle_idx], linewidth=2, 
                           label=f"循环 {i+1}")
                    
                    # 计算并绘制等效刚度线
                    min_disp = min(cycle_disp)
                    max_disp = max(cycle_disp)
                    mid_disp = (min_disp + max_disp) / 2
                    
                    # 使用等效刚度计算力值
                    min_force_fitted = stiffness * (min_disp - mid_disp)
                    max_force_fitted = stiffness * (max_disp - mid_disp)
                    
                    # 绘制等效刚度线
                    ax1.plot([min_disp, max_disp], [min_force_fitted, max_force_fitted], '--', 
                           color=colors[cycle_idx], linewidth=1)
            
            # 设置标签和标题
            ax1.set_xlabel(f"位移 ({self.current_disp_unit})")
            ax1.set_ylabel(f"力 ({self.current_force_unit})")
            ax1.set_title("循环滞回曲线和等效刚度线")
            
            # 添加网格和原点参考线
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax1.axvline(x=0, color='k', linestyle='-', alpha=0.3)
            
            # 绘制刚度变化
            if len(stiffness_values) > 0:
                avg_stiffness = total_stiffness / len(stiffness_values)
                
                # 绘制刚度值
                ax2.plot(cycle_indices, stiffness_values, 'bo-', linewidth=2, markersize=6)
                
                # 绘制平均刚度线
                ax2.axhline(y=avg_stiffness, color='r', linestyle='--', 
                           label=f"平均刚度: {avg_stiffness:.3f} {force_unit}/{disp_unit}")
                
                # 设置标签和标题
                ax2.set_xlabel("循环编号")
                ax2.set_ylabel(f"等效刚度 ({force_unit}/{disp_unit})")
                ax2.set_title("等效刚度变化")
                
                # 设置x轴刻度为整数
                ax2.set_xticks(cycle_indices)
                
                # 添加网格和图例
                ax2.grid(True, linestyle='--', alpha=0.7)
                ax2.legend(loc='best')
            
            # 重新绘制
            self.fig.tight_layout()
            self.canvas.draw()
            
            return True
        
        except Exception as e:
            logger.error(f"绘制循环和等效刚度线出错: {str(e)}")
            return False
    
    def draw_skeleton_curve(self, workcases, skeleton_data, disp_unit="mm", force_unit="kN"):
        """绘制骨架曲线
        
        参数:
            workcases: 工况数据列表
            skeleton_data: 骨架曲线数据
            disp_unit: 位移单位
            force_unit: 力单位
        """
        try:
            # 更新单位
            self.current_disp_unit = disp_unit
            self.current_force_unit = force_unit
            
            # 清空图形
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            
            # 绘制各个工况的滞回曲线
            colors = plt.cm.tab10.colors
            
            for i, workcase in enumerate(workcases):
                cycle_idx = i % len(colors)
                cycle_disp = workcase["displacement"]
                cycle_force = workcase["force"]
                workcase_name = workcase["name"]
                
                ax.plot(cycle_disp, cycle_force, '-', color=colors[cycle_idx], alpha=0.5,
                       label=f"{workcase_name}")
                
                # 标记峰值点
                max_disp_idx = np.argmax(cycle_disp)
                min_disp_idx = np.argmin(cycle_disp)
                
                ax.plot(cycle_disp[max_disp_idx], cycle_force[max_disp_idx], 'o', 
                       color=colors[cycle_idx], markersize=8)
                ax.plot(cycle_disp[min_disp_idx], cycle_force[min_disp_idx], 's', 
                       color=colors[cycle_idx], markersize=8)
            
            # 绘制骨架曲线
            if skeleton_data:
                skeleton_disp = [p[0] for p in skeleton_data]
                skeleton_force = [p[1] for p in skeleton_data]
                
                ax.plot(skeleton_disp, skeleton_force, 'k--', linewidth=2, label="骨架曲线")
            
            # 设置标签和标题
            ax.set_xlabel(f"位移 ({self.current_disp_unit})")
            ax.set_ylabel(f"力 ({self.current_force_unit})")
            ax.set_title("骨架曲线")
            
            # 添加网格和原点参考线
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
            
            # 添加图例
            ax.legend(loc='best')
            
            # 重新绘制
            self.fig.tight_layout()
            self.canvas.draw()
            
            # 更新结果区域
            self.clear_result()
            self.update_result("骨架曲线\n\n")
            self.update_result(f"工况数量: {len(workcases)}\n")
            self.update_result(f"骨架曲线点数: {len(skeleton_data)}\n\n")
            
            for i, workcase in enumerate(workcases):
                workcase_name = workcase["name"]
                stiffness = workcase.get("stiffness", 0)
                energy = workcase.get("energy", 0)
                
                self.update_result(f"工况 {i+1}: {workcase_name}\n")
                self.update_result(f"  等效刚度: {stiffness:.3f} {force_unit}/{disp_unit}\n")
                self.update_result(f"  能量耗散: {energy:.3f}\n\n")
            
            return True
        
        except Exception as e:
            logger.error(f"绘制骨架曲线出错: {str(e)}")
            self.clear_result()
            self.update_result(f"绘制骨架曲线出错: {str(e)}\n")
            return False
    
    def draw_multi_workcase_skeleton(self, workcases, skeleton_data, disp_unit="mm", force_unit="kN"):
        """绘制多工况骨架曲线
        
        参数:
            workcases: 工况数据列表
            skeleton_data: 骨架曲线数据
            disp_unit: 位移单位
            force_unit: 力单位
        """
        try:
            # 更新单位
            self.current_disp_unit = disp_unit
            self.current_force_unit = force_unit
            
            # 清空图形
            self.fig.clear()
            
            # 创建两个子图
            ax1 = self.fig.add_subplot(211)  # 上半部分 - 滞回曲线和骨架曲线
            ax2 = self.fig.add_subplot(212)  # 下半部分 - 刚度对比
            
            # 绘制各个工况的滞回曲线和骨架曲线
            colors = plt.cm.tab10.colors
            stiffness_values = []
            workcase_names = []
            
            for i, workcase in enumerate(workcases):
                cycle_idx = i % len(colors)
                cycle_disp = workcase["displacement"]
                cycle_force = workcase["force"]
                workcase_name = workcase["name"]
                stiffness = workcase.get("stiffness", 0)
                
                # 保存刚度值和工况名
                stiffness_values.append(stiffness)
                workcase_names.append(workcase_name)
                
                # 绘制滞回曲线
                ax1.plot(cycle_disp, cycle_force, '-', color=colors[cycle_idx], alpha=0.5,
                        label=f"{workcase_name}")
                
                # 标记峰值点
                max_disp_idx = np.argmax(cycle_disp)
                min_disp_idx = np.argmin(cycle_disp)
                
                ax1.plot(cycle_disp[max_disp_idx], cycle_force[max_disp_idx], 'o', 
                        color=colors[cycle_idx], markersize=8)
                ax1.plot(cycle_disp[min_disp_idx], cycle_force[min_disp_idx], 's', 
                        color=colors[cycle_idx], markersize=8)
            
            # 绘制骨架曲线
            if skeleton_data:
                skeleton_disp = [p[0] for p in skeleton_data]
                skeleton_force = [p[1] for p in skeleton_data]
                
                ax1.plot(skeleton_disp, skeleton_force, 'k--', linewidth=2, label="骨架曲线")
            
            # 设置标签和标题
            ax1.set_xlabel(f"位移 ({self.current_disp_unit})")
            ax1.set_ylabel(f"力 ({self.current_force_unit})")
            ax1.set_title("多工况骨架曲线")
            
            # 添加网格和原点参考线
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax1.axvline(x=0, color='k', linestyle='-', alpha=0.3)
            
            # 添加图例
            ax1.legend(loc='best')
            
            # 绘制刚度对比条形图
            bar_positions = list(range(len(stiffness_values)))
            bars = ax2.bar(bar_positions, stiffness_values, align='center', alpha=0.7)
            
            # 设置颜色与上图一致
            for i, bar in enumerate(bars):
                bar.set_color(colors[i % len(colors)])
            
            # 设置刻度标签
            ax2.set_xticks(bar_positions)
            ax2.set_xticklabels(workcase_names, rotation=45, ha='right')
            
            # 设置标签和标题
            ax2.set_ylabel(f"等效刚度 ({force_unit}/{disp_unit})")
            ax2.set_title("工况等效刚度对比")
            
            # 添加数值标签
            for i, v in enumerate(stiffness_values):
                ax2.text(i, v + 0.1, f"{v:.2f}", ha='center')
            
            # 添加网格
            ax2.grid(True, linestyle='--', alpha=0.7, axis='y')
            
            # 重新绘制
            self.fig.tight_layout()
            self.canvas.draw()
            
            # 更新结果区域
            self.clear_result()
            self.update_result("多工况骨架曲线\n\n")
            self.update_result(f"工况数量: {len(workcases)}\n")
            self.update_result(f"骨架曲线点数: {len(skeleton_data)}\n\n")
            
            self.update_result(f"{'工况':<6}{'名称':<20}{'位移范围 ('+disp_unit+')':<20}{'等效刚度 ('+force_unit+'/'+disp_unit+')':<20}\n")
            self.update_result("-" * 70 + "\n")
            
            for i, workcase in enumerate(workcases):
                workcase_name = workcase["name"]
                stiffness = workcase.get("stiffness", 0)
                max_disp = workcase.get("max_disp", 0)
                min_disp = workcase.get("min_disp", 0)
                
                self.update_result(f"{i+1:<6}{workcase_name:<20}{min_disp:.3f} ~ {max_disp:.3f}  {stiffness:.3f}\n")
            
            return True
        
        except Exception as e:
            logger.error(f"绘制多工况骨架曲线出错: {str(e)}")
            self.clear_result()
            self.update_result(f"绘制多工况骨架曲线出错: {str(e)}\n")
            return False