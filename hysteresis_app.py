"""
准静态试验滞回曲线分析工具 - 主程序

该模块负责初始化和启动整个应用程序
"""

import tkinter as tk
import logging
from datetime import datetime
import os
import sys
import matplotlib
import utils_visualization as uv
from tkinter import messagebox

# 导入自定义模块
from hysteresis_gui import HysteresisGUI
from hysteresis_controller import HysteresisController

# 设置日志
def setup_logging():
    """设置日志记录"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"hysteresis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    
    return logging.getLogger(__name__)

def create_menu(root, controller):
    """创建菜单栏
    
    参数:
        root: 主窗口
        controller: 控制器对象
    """
    # 创建菜单栏
    menubar = tk.Menu(root)
    
    # 文件菜单
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="打开文件", command=controller.load_file)
    file_menu.add_command(label="打开多个文件", command=controller.load_multiple_files)
    file_menu.add_command(label="打开文件夹", command=controller.load_folder)
    file_menu.add_separator()
    file_menu.add_command(label="退出", command=root.quit)
    menubar.add_cascade(label="文件", menu=file_menu)
    
    # 工具菜单
    tools_menu = tk.Menu(menubar, tearoff=0)
    tools_menu.add_command(label="绘制滞回曲线", command=controller.draw_raw_hysteresis)
    tools_menu.add_command(label="处理数据", command=controller.process_data)
    tools_menu.add_command(label="计算等效刚度", command=controller.show_equivalent_stiffness)
    tools_menu.add_command(label="生成骨架曲线", command=controller.generate_skeleton_curve)
    tools_menu.add_command(label="生成多工况骨架曲线", command=controller.generate_multi_workcase_skeleton)
    menubar.add_cascade(label="工具", menu=tools_menu)
    
    # 帮助菜单
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="关于", command=lambda: show_about_dialog(root))
    menubar.add_cascade(label="帮助", menu=help_menu)
    
    # 设置菜单栏
    root.config(menu=menubar)

def show_about_dialog(root):
    """显示关于对话框
    
    参数:
        root: 主窗口
    """
    about_text = """
准静态试验滞回曲线分析工具

版本: 1.0.0
开发日期: 2025年3月

本工具用于分析准静态试验的滞回曲线数据，实现滞回曲线的可视化、
循环加载识别、等效刚度计算、骨架曲线生成等功能。
    """
    
    # 创建对话框
    dialog = tk.Toplevel(root)
    dialog.title("关于")
    dialog.geometry("400x300")
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()
    
    # 添加文本
    text = tk.Text(dialog, height=15, width=50)
    text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    text.insert(tk.END, about_text)
    text.config(state=tk.DISABLED)
    
    # 添加确定按钮
    button = tk.Button(dialog, text="确定", command=dialog.destroy)
    button.pack(pady=10)
    
    # 居中对话框
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (root.winfo_width() - width) // 2 + root.winfo_x()
    y = (root.winfo_height() - height) // 2 + root.winfo_y()
    dialog.geometry(f"{width}x{height}+{x}+{y}")

def main():
    """主程序入口"""
    # 设置日志
    logger = setup_logging()
    logger.info("程序启动")
    
    try:
        # 设置中文字体
        uv.set_chinese_font()
        
        # 创建主窗口
        root = tk.Tk()
        root.title("准静态试验滞回曲线分析工具")
        root.geometry("1280x800")
        root.minsize(800, 600)
        
        # 先创建一个空的GUI，暂不设置控制器
        gui = HysteresisGUI(root, None)
        
        # 创建真正的控制器
        controller = HysteresisController(gui)
        
        # 将控制器设置到GUI并重新绑定所有按钮
        gui.controller = controller
        gui.rebind_buttons(controller)
        
        # 创建菜单栏
        create_menu(root, controller)
        
        # 显示窗口
        root.mainloop()
        
        logger.info("程序正常退出")
    
    except Exception as e:
        logger.error(f"程序发生错误: {str(e)}", exc_info=True)
        if 'root' in locals():
            messagebox.showerror("错误", f"程序发生错误: {str(e)}")
    
    finally:
        logger.info("程序结束")

if __name__ == "__main__":
    main()