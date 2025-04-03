"""
准静态试验分析工具 - 数据处理模块

该模块包含所有数据加载、处理和分析相关的功能
"""

import os
import pandas as pd
import numpy as np
import logging
import glob
import utils_data as ud

logger = logging.getLogger(__name__)

class HysteresisData:
    """滞回曲线数据处理类"""
    
    def __init__(self):
        """初始化数据处理器"""
        logger.info("初始化数据处理器")
        # 文件相关变量
        self.file_path = None
        self.file_paths = []
        self.current_file_index = 0
        
        # 数据变量
        self.data = None
        self.raw_displacement = None
        self.raw_force = None
        self.processed_displacement = None
        self.processed_force = None
        self.processed_data = None
        self.cycles = None
        self.cycle_features = None
        self.skeleton_data = None
        self.backbone_curve = None
        
        # 工况数据
        self.workcase_data = []
        
        # 设置
        self.skiprows = 0
        
        # 多工况相关
        self.workcases = []
        
        # 通道名称
        self.disp_channel_name = None
        self.force_channel_name = None
        self.force2_channel_name = None
        
        # 处理参数
        self.params = {}
        logger.info("数据处理器初始化完成")
    
    def reset_processed_data(self):
        """重置处理后的数据"""
        logger.debug("重置处理后的数据")
        self.raw_displacement = None
        self.raw_force = None
        self.processed_displacement = None
        self.processed_force = None
        self.processed_data = None
        self.cycles = None
        self.cycle_features = None
        self.skeleton_data = None
        self.backbone_curve = None
        self.params = {}
    
    def load_file(self, file_path, skiprows=0):
        """加载单个文件
        
        参数:
            file_path: 文件路径
            skiprows: 跳过数据前几行
            
        返回:
            tuple: (success, message)
        """
        try:
            logger.info(f"加载文件: {file_path}, skiprows={skiprows}")
            
            # 设置路径和跳过行数
            self.file_path = file_path
            self.file_paths = [file_path]
            self.current_file_index = 0
            self.skiprows = skiprows
            
            # 读取数据
            data, error = ud.read_excel_data(file_path, skiprows)
            
            if error:
                logger.error(f"读取文件出错: {error}")
                return False, f"读取文件出错: {error}"
            
            if data is None or data.empty:
                logger.error("文件数据为空")
                return False, "文件数据为空"
            
            # 保存数据
            self.data = data
            
            # 重置处理后的数据
            self.reset_processed_data()
            
            logger.info(f"成功加载文件: {os.path.basename(file_path)}")
            return True, f"成功加载文件: {os.path.basename(file_path)}"
            
        except Exception as e:
            logger.error(f"加载文件出错: {str(e)}", exc_info=True)
            return False, f"加载文件出错: {str(e)}"
    
    def load_multiple_files(self, file_paths, skiprows=0):
        """加载多个数据文件
        
        参数:
            file_paths: 文件路径列表
            skiprows: 跳过数据前几行
            
        返回:
            tuple: (success, message)
        """
        try:
            if not file_paths:
                return False, "未选择文件"
            
            # 确保file_paths是列表
            file_paths_list = list(file_paths)
            logger.info(f"加载多个文件: {len(file_paths_list)} 个文件")
            
            # 保存文件路径列表和跳过行数
            self.file_paths = file_paths_list.copy()  # 使用.copy()创建一个新的列表副本
            self.current_file_index = 0
            self.skiprows = skiprows  # 设置skiprows实例变量
            
            logger.debug(f"设置skiprows = {skiprows}")
            
            # 加载第一个文件
            success, message = self.load_current_file()
            
            if success:
                logger.info(f"成功加载第一个文件，总共 {len(self.file_paths)} 个文件")
                if len(self.file_paths) > 1:
                    return True, f"已加载 {len(self.file_paths)} 个文件中的第 1 个: {os.path.basename(self.file_path)}"
                else:
                    return True, f"成功加载文件: {os.path.basename(self.file_path)}"
            else:
                logger.error(f"加载第一个文件失败: {message}")
                return False, message
                
        except Exception as e:
            logger.error(f"加载多个文件过程中发生错误: {str(e)}", exc_info=True)
            return False, f"加载多个文件过程中发生错误: {str(e)}"
    
    def load_folder(self, folder_path, file_pattern="*.xlsx"):
        """加载文件夹中的所有数据文件
        
        参数:
            folder_path: 文件夹路径
            file_pattern: 文件匹配模式
            
        返回:
            tuple: (success, message)
        """
        try:
            # 查找匹配的文件
            pattern = os.path.join(folder_path, file_pattern)
            file_paths = glob.glob(pattern)
            
            if not file_paths:
                return False, f"在 {folder_path} 中没有找到 {file_pattern} 文件"
            
            # 按名称排序
            file_paths.sort()
            
            # 设置文件路径列表
            return self.load_multiple_files(file_paths, self.skiprows)
        
        except Exception as e:
            logger.error(f"加载文件夹出错: {str(e)}")
            return False, f"加载文件夹过程中发生错误: {str(e)}"
    
    def load_current_file(self):
        """加载当前索引的文件
        
        返回:
            tuple: (success, message)
        """
        if not self.file_paths or self.current_file_index >= len(self.file_paths):
            logger.error("无效的文件索引")
            return False, "无效的文件索引"
        
        # 获取当前文件路径
        current_path = self.file_paths[self.current_file_index]
        logger.info(f"加载当前文件: {os.path.basename(current_path)}, 索引: {self.current_file_index + 1}/{len(self.file_paths)}")
        
        try:
            # 保存原有的file_paths
            saved_file_paths = self.file_paths.copy()
            saved_current_index = self.current_file_index
            
            # 设置当前文件路径
            self.file_path = current_path
            
            # 读取数据
            data, error = ud.read_excel_data(current_path, self.skiprows)
            
            # 恢复file_paths
            self.file_paths = saved_file_paths
            self.current_file_index = saved_current_index
            
            if error:
                logger.error(f"读取文件出错: {error}")
                return False, f"读取文件出错: {error}"
            
            if data is None or data.empty:
                logger.error("文件数据为空")
                return False, "文件数据为空"
            
            # 保存数据
            self.data = data
            
            # 重置处理后的数据
            self.reset_processed_data()
            
            logger.info(f"成功加载文件: {os.path.basename(current_path)}, file_paths长度: {len(self.file_paths)}")
            return True, f"成功加载文件: {os.path.basename(current_path)}"
            
        except Exception as e:
            logger.error(f"加载文件出错: {str(e)}", exc_info=True)
            return False, f"加载文件过程中发生错误: {str(e)}"
    
    def next_file(self):
        """切换到下一个文件
        
        返回:
            tuple: (success, message)
        """
        if not self.file_paths:
            return False, "没有加载文件"
        
        if self.current_file_index < len(self.file_paths) - 1:
            self.current_file_index += 1
            return self.load_current_file()
        else:
            return False, "已经是最后一个文件"
    
    def prev_file(self):
        """切换到上一个文件
        
        返回:
            tuple: (success, message)
        """
        if not self.file_paths:
            return False, "没有加载文件"
        
        if self.current_file_index > 0:
            self.current_file_index -= 1
            return self.load_current_file()
        else:
            return False, "已经是第一个文件"
    
    def get_data_channels(self):
        """获取数据的所有通道名
        
        返回:
            list: 通道名列表
        """
        if self.data is None:
            logger.error("没有加载数据")
            return []
        
        columns = list(self.data.columns)
        logger.debug(f"获取到 {len(columns)} 个数据通道")
        return columns
    
    def get_current_file_info(self):
        """获取当前文件的信息
        
        返回:
            str: 文件信息字符串
        """
        if not self.file_path:
            return "未选择文件"
        
        file_basename = os.path.basename(self.file_path)
        file_count = len(self.file_paths)
        
        if file_count > 1:
            return f"当前文件: {file_basename} ({self.current_file_index + 1}/{file_count})"
        else:
            return f"当前文件: {file_basename}"
    
    def set_channels(self, disp_channel, force_channel, force2_channel=None):
        """设置位移和力通道
        
        参数:
            disp_channel: 位移通道名
            force_channel: 力通道名
            force2_channel: 第二力通道名，可选
            
        返回:
            tuple: (success, message)
        """
        try:
            logger.info(f"设置通道: 位移={disp_channel}, 力1={force_channel}, 力2={force2_channel}")
            
            if self.data is None:
                logger.error("没有加载数据")
                return False, "没有加载数据"
            
            columns = list(self.data.columns)
            
            if disp_channel not in columns:
                logger.error(f"位移通道 {disp_channel} 不存在")
                return False, f"位移通道 {disp_channel} 不存在"
            
            if force_channel not in columns:
                logger.error(f"力通道 {force_channel} 不存在")
                return False, f"力通道 {force_channel} 不存在"
            
            if force2_channel and force2_channel not in columns:
                logger.error(f"力通道2 {force2_channel} 不存在")
                return False, f"力通道2 {force2_channel} 不存在"
            
            # 设置通道名
            self.disp_channel_name = disp_channel
            self.force_channel_name = force_channel
            self.force2_channel_name = force2_channel
            
            # 提取原始数据
            self.raw_displacement = np.array(self.data[disp_channel])
            self.raw_force = np.array(self.data[force_channel])
            
            # 添加第二个力传感器数据
            if force2_channel:
                force2_data = np.array(self.data[force2_channel])
                self.raw_force = self.raw_force + force2_data
            
            logger.info(f"成功设置通道: 位移={disp_channel}, 力1={force_channel}, 力2={force2_channel}")
            return True, "成功设置通道"
            
        except Exception as e:
            logger.error(f"设置通道出错: {str(e)}", exc_info=True)
            return False, f"设置通道出错: {str(e)}"
    
    def process_data(self, params=None):
        """处理原始数据
        
        参数:
            params: 处理参数字典
            
        返回:
            tuple: (success, message)
        """
        try:
            logger.info("开始处理数据")
            
            if self.raw_displacement is None or self.raw_force is None:
                logger.error("没有设置通道")
                return False, "没有设置通道"
            
            # 默认参数
            default_params = {
                "baseline_correction": True,
                "zero_baseline": True,
                "remove_outliers": True,
                "smooth_data": True,
                "smooth_window": 10,
                "peak_prominence": 0.1,
                "min_cycle_points": 100,
                "cycle_count": 3,
                "start_at_cycle": 0,
                "end_at_cycle": -1,
                "calibrate_units": True
            }
            
            # 更新参数
            self.params = default_params.copy()
            if params:
                self.params.update(params)
            
            logger.debug(f"处理参数: {self.params}")
            
            # 1. 数据预处理
            disp = self.raw_displacement.copy()
            force = self.raw_force.copy()
            
            # 2. 基线校正
            if self.params["baseline_correction"]:
                disp, force = ud.correct_baseline(disp, force)
            
            # 3. 零点校正
            if self.params["zero_baseline"]:
                disp, force = ud.zero_baseline(disp, force)
            
            # 4. 异常值移除
            if self.params["remove_outliers"]:
                disp, force = ud.remove_outliers(disp, force)
            
            # 5. 平滑处理
            if self.params["smooth_data"]:
                disp, force = ud.smooth_data(disp, force, window=self.params["smooth_window"])
            
            # 保存处理后的数据
            self.processed_displacement = disp
            self.processed_force = force
            
            # 组合为处理后的数据
            self.processed_data = np.column_stack((disp, force))
            
            logger.info("数据处理完成")
            return True, "数据处理完成"
            
        except Exception as e:
            logger.error(f"数据处理出错: {str(e)}", exc_info=True)
            return False, f"数据处理出错: {str(e)}"
    
    def identify_cycles(self, peak_prominence=0.1, min_cycle_points=100):
        """识别循环加载
        
        参数:
            peak_prominence: 峰值识别阈值
            min_cycle_points: 一个循环最少点数
            
        返回:
            tuple: (success, message)
        """
        try:
            logger.info(f"开始识别循环加载: peak_prominence={peak_prominence}, min_cycle_points={min_cycle_points}")
            
            if self.processed_displacement is None or self.processed_force is None:
                logger.error("请先处理数据")
                return False, "请先处理数据"
            
            # 获取处理后的数据
            disp = self.processed_displacement
            force = self.processed_force
            
            # 识别循环
            cycles, peaks, valleys = ud.identify_loading_cycles(
                disp, force, prominence=peak_prominence, min_points=min_cycle_points
            )
            
            if len(cycles) == 0:
                logger.warning("未识别到循环加载")
                return False, "未识别到循环加载，请调整识别参数"
            
            # 保存循环数据
            self.cycles = cycles
            self.cycle_peaks = peaks
            self.cycle_valleys = valleys
            
            # 计算每个循环的特征
            self.cycle_features = ud.calculate_cycle_features(cycles, disp, force)
            
            message = f"识别到 {len(cycles)} 个循环加载"
            logger.info(message)
            return True, message
            
        except Exception as e:
            logger.error(f"识别循环加载出错: {str(e)}", exc_info=True)
            return False, f"识别循环加载出错: {str(e)}"
    
    def get_cycle_data(self, cycle_index):
        """获取指定索引的循环数据
        
        参数:
            cycle_index: 循环索引
            
        返回:
            tuple: (x, y) 循环的位移和力数据
        """
        if self.cycles is None or not 0 <= cycle_index < len(self.cycles):
            logger.error(f"无效的循环索引: {cycle_index}")
            return None, None
        
        # 获取循环的索引范围
        start, end = self.cycles[cycle_index]
        
        # 提取位移和力数据
        disp = self.processed_displacement[start:end]
        force = self.processed_force[start:end]
        
        return disp, force
    
    def get_equivalent_stiffness(self, cycle_indices=None):
        """计算指定循环的等效刚度
        
        参数:
            cycle_indices: 循环索引列表，默认为None，表示全部循环
            
        返回:
            tuple: (success, results)
        """
        try:
            if self.cycles is None or self.cycle_features is None:
                logger.error("请先识别循环加载")
                return False, "请先识别循环加载"
            
            # 默认使用全部循环
            if cycle_indices is None:
                cycle_indices = range(len(self.cycles))
            
            results = {}
            
            for idx in cycle_indices:
                if 0 <= idx < len(self.cycles):
                    disp, force = self.get_cycle_data(idx)
                    
                    # 计算刚度和能量耗散
                    stiffness, energy = ud.calculate_stiffness_and_energy(disp, force)
                    
                    # 获取循环特征
                    feature = self.cycle_features[idx] if idx < len(self.cycle_features) else {}
                    
                    # 保存结果
                    results[idx] = {
                        "cycle_index": idx,
                        "stiffness": stiffness,
                        "energy_dissipation": energy,
                        "max_disp": feature.get("max_disp", 0),
                        "min_disp": feature.get("min_disp", 0),
                        "max_force": feature.get("max_force", 0),
                        "min_force": feature.get("min_force", 0),
                        "disp_range": feature.get("disp_range", 0),
                        "force_range": feature.get("force_range", 0)
                    }
            
            logger.info(f"已计算 {len(results)} 个循环的等效刚度")
            return True, results
            
        except Exception as e:
            logger.error(f"计算等效刚度出错: {str(e)}", exc_info=True)
            return False, f"计算等效刚度出错: {str(e)}"
    
    def add_workcase(self, name=None, cycle_index=0):
        """添加当前工况的数据
        
        参数:
            name: 工况名称，默认为当前文件名
            cycle_index: 使用的循环索引
            
        返回:
            tuple: (success, message)
        """
        try:
            if self.cycles is None or cycle_index >= len(self.cycles):
                logger.error("请先识别循环加载")
                return False, "请先识别循环加载或循环索引无效"
            
            # 默认使用文件名作为工况名
            if name is None and self.file_path:
                name = os.path.splitext(os.path.basename(self.file_path))[0]
            
            # 获取指定循环的数据
            disp, force = self.get_cycle_data(cycle_index)
            
            if disp is None or force is None:
                logger.error(f"获取循环 {cycle_index} 数据失败")
                return False, f"获取循环 {cycle_index} 数据失败"
            
            # 获取循环特征
            if self.cycle_features and cycle_index < len(self.cycle_features):
                feature = self.cycle_features[cycle_index]
            else:
                feature = {}
            
            # 计算等效刚度
            stiffness, energy = ud.calculate_stiffness_and_energy(disp, force)
            
            # 创建工况数据
            workcase = {
                "name": name,
                "displacement": disp,
                "force": force,
                "stiffness": stiffness,
                "energy": energy,
                "feature": feature,
                "max_disp": feature.get("max_disp", 0),
                "min_disp": feature.get("min_disp", 0),
                "max_force": feature.get("max_force", 0),
                "min_force": feature.get("min_force", 0)
            }
            
            # 添加到工况列表
            self.workcases.append(workcase)
            
            logger.info(f"已添加工况: {name}, 共 {len(self.workcases)} 个工况")
            return True, f"已添加工况: {name}, 共 {len(self.workcases)} 个工况"
            
        except Exception as e:
            logger.error(f"添加工况出错: {str(e)}", exc_info=True)
            return False, f"添加工况出错: {str(e)}"
    
    def generate_skeleton_curve(self):
        """生成骨架曲线
        
        返回:
            tuple: (success, message)
        """
        try:
            if not self.workcases:
                logger.error("没有工况数据")
                return False, "没有工况数据，请先添加工况"
            
            # 提取所有工况的峰值点
            skeleton_points = []
            
            for wc in self.workcases:
                # 获取位移、力和特征
                disp = wc["displacement"]
                force = wc["force"]
                feature = wc["feature"]
                
                # 获取峰值点
                max_disp_idx = np.argmax(disp)
                min_disp_idx = np.argmin(disp)
                
                # 添加正向峰值点
                skeleton_points.append((disp[max_disp_idx], force[max_disp_idx]))
                
                # 添加负向峰值点
                skeleton_points.append((disp[min_disp_idx], force[min_disp_idx]))
            
            # 按位移排序
            skeleton_points.sort(key=lambda p: p[0])
            
            # 保存骨架曲线
            self.skeleton_data = skeleton_points
            
            message = f"已生成骨架曲线，共 {len(skeleton_points)} 个点"
            logger.info(message)
            return True, message
            
        except Exception as e:
            logger.error(f"生成骨架曲线出错: {str(e)}", exc_info=True)
            return False, f"生成骨架曲线出错: {str(e)}"
    
    def clear_workcases(self):
        """清空工况数据
        
        返回:
            tuple: (success, message)
        """
        try:
            self.workcases = []
            logger.info("已清空所有工况数据")
            return True, "已清空所有工况数据"
        except Exception as e:
            logger.error(f"清空工况数据出错: {str(e)}")
            return False, f"清空工况数据出错: {str(e)}"
    
    def export_results(self, export_path):
        """导出分析结果
        
        参数:
            export_path: 导出文件路径
            
        返回:
            tuple: (success, message)
        """
        try:
            logger.info(f"正在导出结果到: {export_path}")
            
            if not self.cycles or not self.cycle_features:
                logger.error("没有可导出的分析结果")
                return False, "没有可导出的分析结果，请先处理数据"
            
            # 创建结果数据
            results = []
            
            for i, feature in enumerate(self.cycle_features):
                # 计算刚度
                disp, force = self.get_cycle_data(i)
                stiffness, energy = ud.calculate_stiffness_and_energy(disp, force)
                
                # 添加数据
                result = {
                    "循环编号": i + 1,
                    "最大位移": feature.get("max_disp", 0),
                    "最小位移": feature.get("min_disp", 0),
                    "位移范围": feature.get("disp_range", 0),
                    "最大力": feature.get("max_force", 0),
                    "最小力": feature.get("min_force", 0),
                    "力范围": feature.get("force_range", 0),
                    "等效刚度": stiffness,
                    "能量耗散": energy
                }
                
                results.append(result)
            
            # 创建DataFrame并保存
            df = pd.DataFrame(results)
            df.to_excel(export_path, index=False)
            
            logger.info(f"结果已导出到: {export_path}")
            return True, f"结果已导出到: {export_path}"
            
        except Exception as e:
            logger.error(f"导出结果出错: {str(e)}", exc_info=True)
            return False, f"导出结果出错: {str(e)}"