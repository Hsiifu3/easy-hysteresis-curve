"""
准静态试验分析工具 - 控制器模块

该模块负责连接GUI、数据处理和可视化模块，处理用户事件
"""

import logging
import os
import numpy as np
import pandas as pd
from tkinter import filedialog, messagebox
from hysteresis_data import HysteresisData
from hysteresis_viz import HysteresisViz
import utils_data as ud

logger = logging.getLogger(__name__)

class HysteresisController:
    """滞回曲线分析控制器"""
    
    def __init__(self, gui):
        """初始化控制器
        
        参数:
            gui: GUI对象
        """
        logger.info("初始化控制器")
        self.gui = gui
        self.data = HysteresisData()
        self.viz = HysteresisViz(gui.fig, gui.canvas, gui.result_text)
        
        # 将GUI的控制器设置为本控制器
        self.gui.controller = self
        self.gui.rebind_buttons(self)
        
        # 设置单位
        self.update_units()
        
        # 隐藏文件导航按钮
        self.gui.show_file_navigation(False)
        
        logger.info("控制器初始化完成")
    
    def load_file(self):
        """加载单个文件"""
        try:
            logger.info("开始选择单个文件")
            # 弹出文件选择对话框
            file_path = filedialog.askopenfilename(
                title="选择数据文件",
                filetypes=[("Excel文件", "*.xlsx"), ("Excel文件", "*.xls"), ("所有文件", "*.*")]
            )
            
            if not file_path:
                logger.info("用户取消了文件选择")
                return
                
            logger.info(f"选择的文件: {file_path}")
            
            # 获取跳过行数
            skiprows = int(self.gui.skiprows_var.get() or 0)
            
            # 加载文件
            success, message = self.data.load_file(file_path, skiprows)
            
            if success:
                # 更新文件信息
                current_file = os.path.basename(self.data.file_path)
                self.gui.update_file_info(f"当前文件: {current_file}\n路径: {self.data.file_path}")
                
                # 隐藏文件导航按钮
                self.gui.show_file_navigation(False)
                
                # 更新通道选项
                if self.data.data is not None:
                    self.gui.update_channel_options(list(self.data.data.columns))
                
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)
        
        except Exception as e:
            logger.error(f"加载文件出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"加载文件出错: {str(e)}")
    
    def load_multiple_files(self):
        """加载多个文件"""
        try:
            logger.info("开始选择多个文件")
            # 弹出文件选择对话框
            file_paths = filedialog.askopenfilenames(
                title="选择多个数据文件",
                filetypes=[("Excel文件", "*.xlsx"), ("Excel文件", "*.xls"), ("所有文件", "*.*")]
            )
            
            if not file_paths:
                logger.info("用户取消了文件选择")
                return
                
            logger.info(f"文件选择对话框返回值类型: {type(file_paths)}")
            logger.info(f"文件选择对话框返回值: {file_paths}")
            
            # 将tuple转换为list
            if isinstance(file_paths, tuple):
                file_paths = list(file_paths)
                logger.info(f"将非字符串对象转换为列表，转换后长度: {len(file_paths)}")
            
            # 获取当前的skiprows设置
            skiprows = int(self.gui.skiprows_var.get() or 0)
            
            # 加载多个文件
            success, message = self.data.load_multiple_files(file_paths, skiprows)
            
            logger.info(f"load_multiple_files返回: 成功={success}, 消息={message}")
            
            if success:
                # 更新文件信息
                current_file = os.path.basename(self.data.file_path)
                self.gui.update_file_info(
                    f"当前文件: {current_file} ({self.data.current_file_index + 1}/{len(self.data.file_paths)})\n"
                    f"路径: {self.data.file_path}"
                )
                
                logger.info(f"当前文件: {current_file}, 索引: {self.data.current_file_index + 1}/{len(self.data.file_paths)}")
                
                # 显示文件导航按钮
                logger.info("显示文件导航按钮")
                self.gui.show_file_navigation(True)
                
                # 更新通道选项
                if self.data.data is not None:
                    logger.info(f"更新通道选项: {list(self.data.data.columns)}")
                    self.gui.update_channel_options(list(self.data.data.columns))
                
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)
        
        except Exception as e:
            logger.error(f"加载多个文件出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"加载多个文件出错: {str(e)}")
    
    def load_folder(self):
        """加载文件夹中的文件"""
        try:
            logger.info("开始选择文件夹")
            # 打开文件夹选择对话框
            folder_path = filedialog.askdirectory(title="选择数据文件夹")
            
            if not folder_path:
                logger.info("用户取消了文件夹选择")
                return  # 用户取消了选择
                
            logger.info(f"选择的文件夹: {folder_path}")
            
            # 获取当前的skiprows设置
            skiprows = int(self.gui.skiprows_var.get() or 0)
            logger.info(f"跳过行数设置: {skiprows}")
            
            # 更新data对象的skiprows值
            self.data.skiprows = skiprows
            
            # 加载文件夹
            success, message = self.data.load_folder(folder_path)
            
            if success:
                # 更新文件信息
                current_file = os.path.basename(self.data.file_path)
                self.gui.update_file_info(
                    f"当前文件: {current_file} ({self.data.current_file_index + 1}/{len(self.data.file_paths)})\n"
                    f"路径: {self.data.file_path}"
                )
                
                # 显示文件导航按钮
                self.gui.show_file_navigation(True)
                
                # 更新通道选项
                if self.data.data is not None:
                    self.gui.update_channel_options(list(self.data.data.columns))
                
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)
        
        except Exception as e:
            logger.error(f"加载文件夹出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"加载文件夹出错: {str(e)}")
    
    def prev_file(self):
        """切换到上一个文件"""
        try:
            logger.info("尝试切换到上一个文件")
            if not hasattr(self.data, 'file_paths') or not self.data.file_paths:
                logger.warning("没有加载多个文件")
                messagebox.showinfo("提示", "没有加载多个文件")
                return
                
            if self.data.current_file_index > 0:
                old_index = self.data.current_file_index
                logger.debug(f"当前文件索引: {old_index + 1}/{len(self.data.file_paths)}，切换到索引: {old_index}")
                self.data.current_file_index -= 1
                success, message = self.data.load_current_file()
                
                if success:
                    # 更新文件信息
                    current_file = os.path.basename(self.data.file_path)
                    total_files = len(self.data.file_paths)
                    current_index = self.data.current_file_index + 1
                    self.gui.update_file_info(
                        f"当前文件: {current_file} ({current_index}/{total_files})\n"
                        f"路径: {self.data.file_path}"
                    )
                    
                    # 更新通道选项
                    if self.data.data is not None:
                        columns = list(self.data.data.columns)
                        self.gui.update_channel_options(columns)
                        
                    logger.info(f"切换到上一个文件: {current_file}, 索引: {current_index}/{total_files}")
                else:
                    logger.error(f"加载上一个文件失败: {message}")
                    messagebox.showerror("错误", f"加载文件失败: {message}")
            else:
                logger.warning("已经是第一个文件")
                messagebox.showinfo("提示", "已经是第一个文件")
                
        except Exception as e:
            logger.error(f"切换到上一个文件出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"切换到上一个文件出错: {str(e)}")
            
    def next_file(self):
        """切换到下一个文件"""
        try:
            logger.info("尝试切换到下一个文件")
            if not hasattr(self.data, 'file_paths') or not self.data.file_paths:
                logger.warning("没有加载多个文件")
                messagebox.showinfo("提示", "没有加载多个文件")
                return
                
            if self.data.current_file_index < len(self.data.file_paths) - 1:
                old_index = self.data.current_file_index
                logger.debug(f"当前文件索引: {old_index + 1}/{len(self.data.file_paths)}，切换到索引: {old_index + 2}")
                self.data.current_file_index += 1
                success, message = self.data.load_current_file()
                
                if success:
                    # 更新文件信息
                    current_file = os.path.basename(self.data.file_path)
                    total_files = len(self.data.file_paths)
                    current_index = self.data.current_file_index + 1
                    self.gui.update_file_info(
                        f"当前文件: {current_file} ({current_index}/{total_files})\n"
                        f"路径: {self.data.file_path}"
                    )
                    
                    # 更新通道选项
                    if self.data.data is not None:
                        columns = list(self.data.data.columns)
                        self.gui.update_channel_options(columns)
                        
                    logger.info(f"切换到下一个文件: {current_file}, 索引: {current_index}/{total_files}")
                else:
                    logger.error(f"加载下一个文件失败: {message}")
                    messagebox.showerror("错误", f"加载文件失败: {message}")
            else:
                logger.warning("已经是最后一个文件")
                messagebox.showinfo("提示", "已经是最后一个文件")
                
        except Exception as e:
            logger.error(f"切换到下一个文件出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"切换到下一个文件出错: {str(e)}")
    
    def apply_skiprows(self):
        """应用跳过行设置"""
        try:
            skiprows = int(self.gui.skiprows_var.get() or 0)
            logger.info(f"应用跳过行设置: {skiprows}")
            
            if self.data.file_path:
                # 如果已经加载了文件，则重新加载当前文件
                success, message = self.data.load_file(self.data.file_path, skiprows)
                
                if success:
                    messagebox.showinfo("成功", f"已应用跳过行设置: {skiprows}")
                    
                    # 更新通道选项
                    if self.data.data is not None:
                        columns = list(self.data.data.columns)
                        self.gui.update_channel_options(columns)
                else:
                    messagebox.showerror("错误", message)
            else:
                # 如果还没有加载文件，则只更新设置
                self.data.skiprows = skiprows
                messagebox.showinfo("提示", f"已设置跳过行数: {skiprows}")
                
        except ValueError:
            logger.error("跳过行数必须为整数")
            messagebox.showerror("错误", "跳过行数必须为整数")
        except Exception as e:
            logger.error(f"应用跳过行设置出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"应用跳过行设置出错: {str(e)}")
    
    def update_units(self):
        """更新单位设置"""
        # 获取单位设置
        disp_unit = self.gui.disp_unit_var.get()
        force_unit = self.gui.force_unit_var.get()
        logger.info(f"更新单位设置: 位移={disp_unit}, 力={force_unit}")
    
    def draw_raw_hysteresis(self):
        """绘制原始滞回曲线"""
        try:
            logger.info("开始绘制原始滞回曲线")
            if self.data.data is None:
                logger.warning("未加载数据")
                messagebox.showinfo("提示", "请先加载数据文件")
                return
                
            # 获取通道设置
            disp_channel = self.gui.disp_channel_var.get()
            force1_channel = self.gui.force1_channel_var.get()
            force2_channel = self.gui.force2_channel_var.get()
            
            if not disp_channel or not force1_channel:
                logger.warning("未设置通道")
                messagebox.showinfo("提示", "请先选择位移和力通道")
                return
                
            logger.info(f"选择的通道: 位移={disp_channel}, 力1={force1_channel}, 力2={force2_channel}")
            
            # 设置通道
            success, message = self.data.set_channels(disp_channel, force1_channel, force2_channel)
            
            if not success:
                logger.error(f"设置通道失败: {message}")
                messagebox.showerror("错误", message)
                return
                
            # 绘制原始滞回曲线
            disp_unit = self.gui.disp_unit_var.get()
            force_unit = self.gui.force_unit_var.get()
            
            self.viz.draw_raw_hysteresis(
                self.data.raw_displacement, 
                self.data.raw_force,
                disp_unit=disp_unit,
                force_unit=force_unit
            )
            
            logger.info("绘制原始滞回曲线完成")
            
        except Exception as e:
            logger.error(f"绘制原始滞回曲线出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"绘制原始滞回曲线出错: {str(e)}")
    
    def process_data(self, silent=False):
        """处理数据
        
        参数:
            silent: 是否静默处理（不显示提示）
        
        返回:
            bool: 处理是否成功
        """
        try:
            logger.info("开始处理数据")
            if self.data.raw_displacement is None or self.data.raw_force is None:
                if not silent:
                    logger.warning("未设置通道")
                    messagebox.showinfo("提示", "请先选择通道并绘制原始滞回曲线")
                return False
                
            # 获取处理参数
            peak_prominence = float(self.gui.peak_prominence_var.get())
            cycle_count = int(self.gui.cycle_count_var.get())
            
            # 处理数据并识别循环
            success_process, message_process = self.data.process_data()
            if not success_process:
                if not silent:
                    logger.error(f"数据处理失败: {message_process}")
                    messagebox.showerror("错误", message_process)
                return False
                
            success_cycles, message_cycles = self.data.identify_cycles(
                peak_prominence=peak_prominence,
                min_cycle_points=100
            )
            
            # 绘制处理后的滞回曲线和识别的循环
            disp_unit = self.gui.disp_unit_var.get()
            force_unit = self.gui.force_unit_var.get()
            
            self.viz.draw_processed_hysteresis_with_cycles(
                self.data.processed_displacement,
                self.data.processed_force,
                self.data.cycles,
                self.data.cycle_peaks,
                self.data.cycle_valleys,
                disp_unit=disp_unit,
                force_unit=force_unit
            )
            
            if not silent and success_cycles:
                messagebox.showinfo("成功", message_cycles)
            
            logger.info("数据处理完成")
            return success_cycles
            
        except Exception as e:
            if not silent:
                logger.error(f"处理数据出错: {str(e)}", exc_info=True)
                messagebox.showerror("错误", f"处理数据出错: {str(e)}")
            return False
    
    def show_equivalent_stiffness(self):
        """计算并显示等效刚度"""
        try:
            logger.info("开始计算等效刚度")
            if self.data.cycles is None:
                logger.warning("未处理数据")
                # 尝试自动处理数据
                if not self.process_data(silent=True):
                    messagebox.showinfo("提示", "请先处理数据并识别循环")
                    return
                
            # 计算等效刚度
            success, results = self.data.get_equivalent_stiffness()
            
            if not success:
                logger.error(f"计算等效刚度失败: {results}")
                messagebox.showerror("错误", f"计算等效刚度失败: {results}")
                return
                
            # 获取单位
            disp_unit = self.gui.disp_unit_var.get()
            force_unit = self.gui.force_unit_var.get()
            
            # 显示等效刚度结果
            self.viz.show_equivalent_stiffness_results(
                results, disp_unit, force_unit
            )
            
            # 绘制循环刚度图
            self.viz.draw_cycles_with_stiffness(
                self.data.processed_displacement,
                self.data.processed_force,
                self.data.cycles,
                results,
                disp_unit=disp_unit,
                force_unit=force_unit
            )
            
            logger.info("计算等效刚度完成")
            
        except Exception as e:
            logger.error(f"计算等效刚度出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"计算等效刚度出错: {str(e)}")
    
    def add_current_workcase(self):
        """添加当前工况数据"""
        try:
            logger.info("开始添加当前工况")
            if self.data.cycles is None:
                logger.warning("未处理数据")
                messagebox.showinfo("提示", "请先处理数据并识别循环")
                return
                
            # 获取文件名作为工况名
            name = os.path.splitext(os.path.basename(self.data.file_path))[0]
            
            # 使用第一个循环作为工况数据
            success, message = self.data.add_workcase(name=name, cycle_index=0)
            
            if success:
                logger.info(f"成功添加工况: {name}")
                messagebox.showinfo("成功", message)
            else:
                logger.error(f"添加工况失败: {message}")
                messagebox.showerror("错误", message)
                
        except Exception as e:
            logger.error(f"添加工况出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"添加工况出错: {str(e)}")
    
    def clear_workcase_data(self):
        """清除工况数据"""
        try:
            logger.info("开始清除工况数据")
            if not self.data.workcases:
                logger.warning("没有工况数据")
                messagebox.showinfo("提示", "没有工况数据")
                return
                
            # 弹出确认对话框
            result = messagebox.askyesno("确认", "确定要清除所有工况数据吗？")
            
            if result:
                # 用户确认，清除工况数据
                success, message = self.data.clear_workcases()
                
                if success:
                    logger.info("成功清除工况数据")
                    messagebox.showinfo("成功", message)
                else:
                    logger.error(f"清除工况数据失败: {message}")
                    messagebox.showerror("错误", message)
            else:
                # 用户取消
                logger.info("用户取消了清除工况数据操作")
                
        except Exception as e:
            logger.error(f"清除工况数据出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"清除工况数据出错: {str(e)}")
    
    def generate_skeleton_curve(self):
        """生成骨架曲线"""
        try:
            logger.info("开始生成骨架曲线")
            if not self.data.workcases:
                logger.warning("没有工况数据")
                # 如果没有工况数据，尝试添加当前工况
                current_file = os.path.basename(self.data.file_path) if self.data.file_path else "未知文件"
                result = messagebox.askyesno(
                    "提示", 
                    f"没有工况数据。是否要添加当前数据 ({current_file}) 作为工况？"
                )
                
                if result:
                    # 用户同意，添加当前工况
                    self.add_current_workcase()
                    if not self.data.workcases:
                        # 添加失败
                        return
                else:
                    # 用户取消
                    return
                
            # 生成骨架曲线
            success, message = self.data.generate_skeleton_curve()
            
            if not success:
                logger.error(f"生成骨架曲线失败: {message}")
                messagebox.showerror("错误", message)
                return
                
            # 获取单位
            disp_unit = self.gui.disp_unit_var.get()
            force_unit = self.gui.force_unit_var.get()
            
            # 绘制骨架曲线
            self.viz.draw_skeleton_curve(
                self.data.workcases,
                self.data.skeleton_data,
                disp_unit=disp_unit,
                force_unit=force_unit
            )
            
            logger.info("生成骨架曲线完成")
            messagebox.showinfo("成功", message)
            
        except Exception as e:
            logger.error(f"生成骨架曲线出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"生成骨架曲线出错: {str(e)}")
    
    def generate_multi_workcase_skeleton(self):
        """生成多工况骨架曲线"""
        try:
            logger.info("开始生成多工况骨架曲线")
            if not self.data.workcases:
                logger.warning("没有工况数据")
                messagebox.showinfo("提示", "请先添加工况数据")
                return
                
            # 生成骨架曲线
            success, message = self.data.generate_skeleton_curve()
            
            if not success:
                logger.error(f"生成骨架曲线失败: {message}")
                messagebox.showerror("错误", message)
                return
                
            # 获取单位
            disp_unit = self.gui.disp_unit_var.get()
            force_unit = self.gui.force_unit_var.get()
            
            # 绘制多工况骨架曲线
            self.viz.draw_multi_workcase_skeleton(
                self.data.workcases,
                self.data.skeleton_data,
                disp_unit=disp_unit,
                force_unit=force_unit
            )
            
            logger.info("生成多工况骨架曲线完成")
            messagebox.showinfo("成功", message)
            
        except Exception as e:
            logger.error(f"生成多工况骨架曲线出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"生成多工况骨架曲线出错: {str(e)}")
    
    def export_results(self):
        """导出分析结果"""
        try:
            logger.info("开始导出分析结果")
            if self.data.cycles is None:
                logger.warning("未处理数据")
                messagebox.showinfo("提示", "请先处理数据并识别循环")
                return
                
            # 弹出文件保存对话框
            file_path = filedialog.asksaveasfilename(
                title="保存分析结果",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )
            
            if not file_path:
                logger.info("用户取消了导出操作")
                return
                
            # 导出结果
            success, message = self.data.export_results(file_path)
            
            if success:
                logger.info(f"成功导出结果到: {file_path}")
                messagebox.showinfo("成功", message)
            else:
                logger.error(f"导出结果失败: {message}")
                messagebox.showerror("错误", message)
                
        except Exception as e:
            logger.error(f"导出分析结果出错: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"导出分析结果出错: {str(e)}")