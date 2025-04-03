"""
准静态试验分析工具 - 图形界面模块

该模块包含所有GUI相关的组件创建和管理代码
"""

import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)

class HysteresisGUI:
    """滞回曲线分析工具的图形界面管理类"""
    
    def __init__(self, master, controller):
        """初始化GUI管理器
        
        参数:
            master: tkinter主窗口
            controller: 控制器对象，用于处理事件
        """
        logger.info("初始化GUI界面")
        self.master = master
        self.controller = controller if controller is not None else DummyController()
        self.setup_chinese_font()
        
        # 初始化组件变量
        self.init_variables()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.master, padding=5)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左侧控制面板
        self.control_frame = ttk.LabelFrame(self.main_frame, text="控制面板")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 创建右侧图表和结果区域
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建图表区域
        self.plot_frame = ttk.LabelFrame(self.right_frame, text="图表显示")
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建结果显示区域
        self.result_frame = ttk.LabelFrame(self.right_frame, text="计算结果")
        self.result_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # 创建图表区域
        self.create_plot_area()
        
        # 创建结果显示区域
        self.create_result_area()
        
        # 创建各个功能区域
        self.create_file_selection_area()
        self.create_channel_selection_area()
        self.create_unit_settings_area()
        self.create_cycle_settings_area()
        self.create_function_buttons()
        self.create_workcase_management_area()
        self.create_batch_processing_area()
        
        logger.info("GUI界面初始化完成")

    def init_variables(self):
        """初始化界面变量"""
        # 文件信息变量
        self.file_info_var = tk.StringVar(value="未选择文件")
        
        # 单位选择变量
        self.disp_units = ["mm", "cm", "m", "in"]
        self.force_units = ["N", "kN", "lbf"]
        self.disp_unit_var = tk.StringVar(value="mm")
        self.force_unit_var = tk.StringVar(value="kN")
        
        # 通道选择变量
        self.disp_channel_var = tk.StringVar()
        self.force1_channel_var = tk.StringVar()
        self.force2_channel_var = tk.StringVar()
        
        # 循环加载设置变量
        self.cycle_count_var = tk.StringVar(value="3")
        self.peak_prominence_var = tk.StringVar(value="0.1")
        
        # 文件读取设置变量
        self.skiprows_var = tk.StringVar(value="0")
    
    def setup_chinese_font(self):
        """设置中文字体"""
        self.default_font = ('SimHei', 9)
    
    def create_plot_area(self):
        """创建图表区域"""
        # 使用更大的图形尺寸
        self.fig = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar_frame = tk.Frame(self.plot_frame)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
    
    def create_result_area(self):
        """创建结果显示区域"""
        # 已经在__init__中创建了结果框架，这里只创建文本区域
        self.result_text = tk.Text(self.result_frame, height=8, font=('SimHei', 10))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.result_text, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
    
    def create_file_selection_area(self):
        """创建文件选择区域"""
        logger.debug("创建文件选择区域")
        file_frame = ttk.LabelFrame(self.control_frame, text="文件选择")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建按钮并添加点击日志
        load_file_btn = ttk.Button(file_frame, text="选择单个文件", 
                  command=lambda: self.log_button_click("选择单个文件", self.controller.load_file))
        load_file_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        load_multiple_btn = ttk.Button(file_frame, text="选择多个文件", 
                  command=lambda: self.log_button_click("选择多个文件", self.controller.load_multiple_files))
        load_multiple_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        load_folder_btn = ttk.Button(file_frame, text="选择文件夹", 
                  command=lambda: self.log_button_click("选择文件夹", self.controller.load_folder))
        load_folder_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 文件读取设置
        file_setting_frame = ttk.Frame(file_frame)
        file_setting_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(file_setting_frame, text="跳过数据前几行:").pack(side=tk.LEFT)
        self.skiprows_entry = ttk.Entry(file_setting_frame, textvariable=self.skiprows_var, width=5)
        self.skiprows_entry.pack(side=tk.LEFT, padx=5)
        apply_btn = ttk.Button(file_setting_frame, text="应用", 
                  command=lambda: self.log_button_click("应用跳过行设置", self.controller.apply_skiprows))
        apply_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加提示说明
        ttk.Label(file_setting_frame, text="(不包括标题行)", 
                 foreground="gray").pack(side=tk.LEFT, padx=5)
        
        # 文件信息显示
        ttk.Label(file_frame, textvariable=self.file_info_var, 
                 wraplength=250).pack(fill=tk.X, padx=5, pady=5)
        
        # 文件导航（当有多个文件时）
        self.file_nav_frame = ttk.Frame(file_frame)
        self.file_nav_frame.pack(fill=tk.X, padx=5, pady=5)
        self.prev_file_btn = ttk.Button(self.file_nav_frame, text="上一个文件", 
                  command=lambda: self.log_button_click("上一个文件", 
                                 lambda: self.controller.prev_file() if self.controller else None))
        self.prev_file_btn.pack(side=tk.LEFT, padx=5)
        self.next_file_btn = ttk.Button(self.file_nav_frame, text="下一个文件", 
                  command=lambda: self.log_button_click("下一个文件", 
                                 lambda: self.controller.next_file() if self.controller else None))
        self.next_file_btn.pack(side=tk.LEFT, padx=5)
        self.file_nav_frame.pack_forget()  # 默认隐藏
    
    def create_channel_selection_area(self):
        """创建通道选择区域"""
        channel_frame = ttk.LabelFrame(self.control_frame, text="通道选择")
        channel_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 位移通道
        disp_frame = ttk.Frame(channel_frame)
        disp_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(disp_frame, text="位移通道:").pack(side=tk.LEFT)
        self.disp_channel_combo = ttk.Combobox(disp_frame, textvariable=self.disp_channel_var, state="readonly")
        self.disp_channel_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 力传感器通道1
        force1_frame = ttk.Frame(channel_frame)
        force1_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(force1_frame, text="力传感器通道1:").pack(side=tk.LEFT)
        self.force1_channel_combo = ttk.Combobox(force1_frame, textvariable=self.force1_channel_var, state="readonly")
        self.force1_channel_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 力传感器通道2
        force2_frame = ttk.Frame(channel_frame)
        force2_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(force2_frame, text="力传感器通道2:").pack(side=tk.LEFT)
        self.force2_channel_combo = ttk.Combobox(force2_frame, textvariable=self.force2_channel_var, state="readonly")
        self.force2_channel_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def create_unit_settings_area(self):
        """创建单位设置区域"""
        unit_frame = ttk.LabelFrame(self.control_frame, text="单位设置")
        unit_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 位移单位
        disp_unit_frame = ttk.Frame(unit_frame)
        disp_unit_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(disp_unit_frame, text="位移单位:").pack(side=tk.LEFT)
        self.disp_unit_combo = ttk.Combobox(disp_unit_frame, textvariable=self.disp_unit_var, 
                                          values=self.disp_units, state="readonly", width=10)
        self.disp_unit_combo.pack(side=tk.LEFT, padx=5)
        self.disp_unit_combo.bind("<<ComboboxSelected>>", 
                                 lambda e: self.controller.update_units())
        
        # 力单位
        force_unit_frame = ttk.Frame(unit_frame)
        force_unit_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(force_unit_frame, text="力单位:").pack(side=tk.LEFT)
        self.force_unit_combo = ttk.Combobox(force_unit_frame, textvariable=self.force_unit_var, 
                                           values=self.force_units, state="readonly", width=10)
        self.force_unit_combo.pack(side=tk.LEFT, padx=5)
        self.force_unit_combo.bind("<<ComboboxSelected>>", 
                                  lambda e: self.controller.update_units())
    
    def create_cycle_settings_area(self):
        """创建循环加载设置区域"""
        cycle_frame = ttk.LabelFrame(self.control_frame, text="循环加载设置")
        cycle_frame.pack(fill=tk.X, padx=5, pady=5)
        
        cycle_input_frame = ttk.Frame(cycle_frame)
        cycle_input_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(cycle_input_frame, text="循环圈数:").pack(side=tk.LEFT)
        self.cycle_count_entry = ttk.Entry(cycle_input_frame, textvariable=self.cycle_count_var, width=10)
        self.cycle_count_entry.pack(side=tk.LEFT, padx=5)
        
        # 峰值识别参数
        peak_frame = ttk.Frame(cycle_frame)
        peak_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(peak_frame, text="峰值识别阈值(0-1):").pack(side=tk.LEFT)
        self.peak_prominence_entry = ttk.Entry(peak_frame, textvariable=self.peak_prominence_var, width=10)
        self.peak_prominence_entry.pack(side=tk.LEFT, padx=5)
    
    def create_function_buttons(self):
        """创建主要功能按钮"""
        logger.debug("创建主要功能按钮")
        button_frame = ttk.LabelFrame(self.control_frame, text="数据处理")
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # A all buttons are in the same row, add logging
        ttk.Button(button_frame, text="1.绘制滞回曲线", 
                  command=lambda: self.log_button_click("绘制滞回曲线", self.controller.draw_raw_hysteresis), 
                  width=14).pack(side=tk.LEFT, padx=3, pady=5)
        ttk.Button(button_frame, text="2.处理数据", 
                  command=lambda: self.log_button_click("处理数据", self.controller.process_data), 
                  width=14).pack(side=tk.LEFT, padx=3, pady=5)
        ttk.Button(button_frame, text="3.计算等效刚度", 
                  command=lambda: self.log_button_click("计算等效刚度", self.controller.show_equivalent_stiffness), 
                  width=14).pack(side=tk.LEFT, padx=3, pady=5)
    
    def create_workcase_management_area(self):
        """创建工况管理区域"""
        return self.create_workcase_frame()
    
    def create_batch_processing_area(self):
        """创建批量处理区域"""
        logger.debug("创建批量处理区域")
        batch_frame = ttk.LabelFrame(self.control_frame, text="批量处理")
        batch_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加按钮，带日志记录
        ttk.Button(batch_frame, text="批量处理文件", 
                  command=lambda: self.log_button_click("批量处理文件", self.controller.batch_process_all), 
                  width=15).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(batch_frame, text="多文件比较", 
                  command=lambda: self.log_button_click("多文件比较", self.controller.show_multi_raw_comparison), 
                  width=15).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(batch_frame, text="导出结果", 
                  command=lambda: self.log_button_click("导出结果", self.controller.export_results), 
                  width=15).pack(side=tk.LEFT, padx=5, pady=5)
    
    def update_file_info(self, info_text):
        """更新文件信息显示"""
        logger.debug(f"更新文件信息: {info_text}")
        self.file_info_var.set(info_text)
    
    def update_result(self, text):
        """向结果区域添加文本"""
        logger.debug(f"更新结果区域: {text[:50]}...")  # 只记录前50个字符，避免日志过长
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)
    
    def clear_result(self):
        """清空结果区域"""
        logger.debug("清空结果区域")
        self.result_text.delete(1.0, tk.END)
    
    def show_file_navigation(self, show=True):
        """显示或隐藏文件导航按钮"""
        if show:
            logger.debug("显示文件导航按钮")
            self.file_nav_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            logger.debug("隐藏文件导航按钮")
            self.file_nav_frame.pack_forget()
    
    def update_channel_options(self, channels):
        """更新通道选择下拉框的选项"""
        logger.debug(f"更新通道选项，共 {len(channels)} 个通道")
        self.disp_channel_combo['values'] = channels
        self.force1_channel_combo['values'] = channels
        self.force2_channel_combo['values'] = channels
        
        # 如果当前值不在选项中，设置为第一个选项
        if self.disp_channel_var.get() not in channels and channels:
            logger.debug(f"设置默认位移通道: {channels[0]}")
            self.disp_channel_var.set(channels[0])
        if self.force1_channel_var.get() not in channels and channels:
            logger.debug(f"设置默认力通道1: {channels[0]}")
            self.force1_channel_var.set(channels[0])
        if self.force2_channel_var.get() not in channels and channels:
            logger.debug("清空力通道2")
            self.force2_channel_var.set("")
    
    def get_values(self):
        """获取所有GUI设置值"""
        values = {
            'skiprows': int(self.skiprows_var.get() or 0),
            'disp_channel': self.disp_channel_var.get(),
            'force1_channel': self.force1_channel_var.get(),
            'force2_channel': self.force2_channel_var.get(),
            'disp_unit': self.disp_unit_var.get(),
            'force_unit': self.force_unit_var.get(),
            'cycle_count': int(self.cycle_count_var.get() or 3),
            'peak_prominence': float(self.peak_prominence_var.get() or 0.1)
        }
        logger.debug(f"获取GUI设置值: {values}")
        return values
    
    def rebind_buttons(self, controller):
        """重新绑定按钮到新的控制器
        
        参数:
            controller: 新的控制器对象
        """
        logger.info(f"重新绑定按钮到控制器: {controller.__class__.__name__}")
        # 直接重新绑定文件导航按钮
        self.prev_file_btn.config(command=lambda: self.log_button_click("上一个文件", controller.prev_file))
        self.next_file_btn.config(command=lambda: self.log_button_click("下一个文件", controller.next_file))
        
        # 更新所有子窗口中的按钮绑定
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        # 判断按钮文本，重新绑定对应的函数
                        if child['text'] == "选择单个文件":
                            child.config(command=lambda: self.log_button_click("选择单个文件", controller.load_file))
                        elif child['text'] == "选择多个文件":
                            child.config(command=lambda: self.log_button_click("选择多个文件", controller.load_multiple_files))
                        elif child['text'] == "选择文件夹":
                            child.config(command=lambda: self.log_button_click("选择文件夹", controller.load_folder))
                        elif child['text'] == "应用":
                            child.config(command=lambda: self.log_button_click("应用跳过行设置", controller.apply_skiprows))
                        elif child['text'] == "1.绘制滞回曲线":
                            child.config(command=lambda: self.log_button_click("绘制滞回曲线", controller.draw_raw_hysteresis))
                        elif child['text'] == "2.处理数据":
                            child.config(command=lambda: self.log_button_click("处理数据", controller.process_data))
                        elif child['text'] == "3.计算等效刚度":
                            child.config(command=lambda: self.log_button_click("计算等效刚度", controller.show_equivalent_stiffness))
                        elif child['text'] == "添加为工况":
                            child.config(command=lambda: self.log_button_click("添加为工况", controller.add_current_as_workcase))
                        elif child['text'] == "生成多工况骨架曲线":
                            child.config(command=lambda: self.log_button_click("生成多工况骨架曲线", controller.generate_multi_workcase_skeleton))
                        elif child['text'] == "清空工况数据":
                            child.config(command=lambda: self.log_button_click("清空工况数据", controller.clear_workcase_data))
                        elif child['text'] == "生成骨架曲线":
                            child.config(command=lambda: self.log_button_click("生成骨架曲线", controller.generate_skeleton_curve))
                        elif child['text'] == "批量处理文件":
                            child.config(command=lambda: self.log_button_click("批量处理文件", controller.batch_process_all))
                        elif child['text'] == "多文件比较":
                            child.config(command=lambda: self.log_button_click("多文件比较", controller.show_multi_raw_comparison))
                        elif child['text'] == "导出结果":
                            child.config(command=lambda: self.log_button_click("导出结果", controller.export_results))
    
    def create_workcase_frame(self):
        """创建工况处理区域"""
        logger.debug("创建工况处理区域")
        # 创建工况处理框架
        workcase_frame = ttk.LabelFrame(self.control_frame, text="工况操作")
        workcase_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 添加为工况按钮，带日志记录
        ttk.Button(workcase_frame, text="添加为工况", 
                  command=lambda: self.log_button_click("添加为工况", 
                                self.controller.add_current_as_workcase if self.controller else None), 
                  width=15).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 生成多工况骨架曲线按钮，带日志记录
        ttk.Button(workcase_frame, text="生成多工况骨架曲线", 
                  command=lambda: self.log_button_click("生成多工况骨架曲线", 
                                self.controller.generate_multi_workcase_skeleton if self.controller else None), 
                  width=20).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 清空工况数据按钮，带日志记录
        ttk.Button(workcase_frame, text="清空工况数据", 
                  command=lambda: self.log_button_click("清空工况数据", 
                                self.controller.clear_workcase_data if self.controller else None), 
                  width=15).pack(side=tk.LEFT, padx=5, pady=5)
        
        return workcase_frame

    # 添加按钮点击日志记录的辅助方法
    def log_button_click(self, button_name, callback_function):
        """记录按钮点击并调用对应的回调函数
        
        参数:
            button_name: 按钮名称
            callback_function: 回调函数
        """
        logger.info(f"点击按钮: {button_name}")
        try:
            callback_function()
        except Exception as e:
            logger.error(f"按钮 '{button_name}' 执行出错: {str(e)}", exc_info=True)

# 定义一个临时控制器类
class DummyController:
    """空控制器，仅用于初始化"""
    def __init__(self):
        pass
    
    def load_file(self):
        pass
    
    def load_multiple_files(self):
        pass
    
    def load_folder(self):
        pass
    
    def apply_skiprows(self):
        pass
    
    def prev_file(self):
        pass
    
    def next_file(self):
        pass
    
    def draw_raw_hysteresis(self):
        pass
    
    def process_data(self):
        pass
    
    def show_equivalent_stiffness(self):
        pass
    
    def debug_cycle_detection(self):
        pass
    
    def generate_skeleton_curve(self):
        pass
    
    def add_current_workcase(self):
        pass
    
    def add_current_as_workcase(self):
        pass
    
    def generate_multi_workcase_skeleton(self):
        pass
    
    def clear_workcase_data(self):
        pass
    
    def batch_process_all(self):
        pass
    
    def show_multi_raw_comparison(self):
        pass
    
    def export_results(self):
        pass
    
    def update_units(self):
        pass