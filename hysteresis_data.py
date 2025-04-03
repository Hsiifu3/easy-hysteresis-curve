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
    
    def extract_channel_data(self, disp_channel, force1_channel, force2_channel=None):
        """提取通道数据
        
        参数:
            disp_channel: 位移通道名称
            force1_channel: 力通道1名称
            force2_channel: 力通道2名称(可选)
            
        返回:
            tuple: (success, message)
        """
        if self.data is None:
            return False, "没有加载数据"
        
        # 提取通道数据
        disp, force, error = ud.extract_channel_data(
            self.data, disp_channel, force1_channel, force2_channel
        )
        
        if error:
            return False, f"提取通道数据出错: {error}"
        
        # 保存通道名称
        self.disp_channel_name = disp_channel
        self.force_channel_name = force1_channel
        self.force2_channel_name = force2_channel
        
        # 保存原始数据
        self.raw_displacement = disp
        self.raw_force = force
        
        return True, "成功提取通道数据"
    
    def process_data(self, cycle_count=3, peak_prominence=0.1):
        """处理数据，识别循环
        
        参数:
            cycle_count: 循环次数
            peak_prominence: 峰值识别阈值
            
        返回:
            tuple: (success, message)
        """
        try:
            if self.data is None or self.data.empty:
                return False, "没有数据可处理"
            
            # 检查是否已经提取了通道数据
            if self.raw_displacement is None or self.raw_force is None:
                return False, "请先提取通道数据（使用extract_channel_data）"
            
            # 预处理数据
            disp_processed, force_processed, _ = ud.preprocess_data(self.raw_displacement, self.raw_force)
            
            # 保存预处理后的数据
            self.processed_displacement = disp_processed
            self.processed_force = force_processed
            self.processed_data = (disp_processed, force_processed)
            
            # 识别循环
            cycles, cycle_features, error = ud.identify_cycles_by_direction(
                disp_processed, 
                force_processed, 
                cycle_count=cycle_count,
                min_prominence=peak_prominence,
                start_threshold=0.05
            )
            
            if error:
                return False, f"循环识别失败: {error}"
            
            # 保存循环数据
            self.cycles = cycles
            self.cycle_features = cycle_features
            
            # 保存处理参数
            self.params = {
                'displacement_channel': getattr(self, 'disp_channel_name', None),
                'force_channel': getattr(self, 'force_channel_name', None),
                'force2_channel': getattr(self, 'force2_channel_name', None),
                'cycle_count': cycle_count,
                'peak_prominence': peak_prominence
            }
            
            return True, f"成功识别 {len(cycles)} 个循环"
            
        except Exception as e:
            logger.error(f"处理数据出错: {str(e)}", exc_info=True)
            return False, f"处理数据出错: {str(e)}"
    
    def calculate_stiffness(self):
        """计算等效刚度
        
        返回:
            tuple: (success, results, message)
        """
        try:
            if self.cycles is None or not self.cycles:
                return False, None, "没有循环数据可以计算刚度"
            
            if self.cycle_features is None or not self.cycle_features:
                return False, None, "没有循环特征点数据可以计算刚度"
            
            # 计算每个循环的等效刚度
            cycle_stiffness = {}
            all_stiffness = []
            
            for cycle_num, features in self.cycle_features.items():
                pos_peak = features.get('positive_peak')
                neg_peak = features.get('negative_peak')
                
                if pos_peak and neg_peak:
                    pos_x, pos_y = pos_peak
                    neg_x, neg_y = neg_peak
                    
                    # 计算等效刚度 (斜率)
                    delta_x = pos_x - neg_x
                    delta_y = pos_y - neg_y
                    
                    if abs(delta_x) > 1e-10:  # 避免除零错误
                        stiffness = delta_y / delta_x
                        
                        # 保存到结果字典
                        cycle_stiffness[cycle_num] = {
                            'equivalent': stiffness,
                            'max_disp': pos_x,
                            'min_disp': neg_x,
                            'max_disp_force': pos_y,
                            'min_disp_force': neg_y
                        }
                        
                        all_stiffness.append(stiffness)
            
            # 计算平均等效刚度
            avg_stiffness = sum(all_stiffness) / len(all_stiffness) if all_stiffness else 0
            
            # 返回结果
            results = {
                'cycle_stiffness': cycle_stiffness,
                'avg_stiffness': avg_stiffness,
                'displacement': self.processed_data[0] if self.processed_data else None,
                'force': self.processed_data[1] if self.processed_data else None
            }
            
            return True, results, ""
            
        except Exception as e:
            logger.error(f"计算等效刚度出错: {str(e)}", exc_info=True)
            return False, None, f"计算等效刚度出错: {str(e)}"
    
    def generate_skeleton_curve(self):
        """生成骨架曲线
        
        返回:
            tuple: (success, skeleton_data, message)
        """
        if self.cycles is None or self.cycle_features is None:
            return False, None, "没有循环数据，请先处理数据"
        
        try:
            # 生成骨架曲线
            skeleton_disp, skeleton_force, error = ud.generate_skeleton_curve_improved(
                self.cycles, self.cycle_features
            )
            
            if error:
                return False, None, f"生成骨架曲线出错: {error}"
            
            # 保存骨架曲线数据
            self.skeleton_data = (skeleton_disp, skeleton_force)
            
            return True, self.skeleton_data, "成功生成骨架曲线"
        
        except Exception as e:
            logger.error(f"生成骨架曲线出错: {str(e)}")
            return False, None, f"生成骨架曲线过程中发生错误: {str(e)}"
    
    def add_workcase(self, name=None):
        """添加当前工况到工况列表
        
        参数:
            name: 工况名称，默认为文件名
            
        返回:
            tuple: (success, message)
        """
        if self.processed_data is None or self.cycles is None:
            return False, "没有处理过的数据，请先处理数据"
        
        try:
            # 如果没有指定名称，使用文件名
            if name is None and self.file_path:
                name = os.path.basename(self.file_path)
            elif name is None:
                name = f"工况 {len(self.workcase_data) + 1}"
            
            # 创建工况数据
            workcase = {
                'name': name,
                'file_path': self.file_path,
                'processed_data': self.processed_data,
                'cycles': self.cycles,
                'cycle_features': self.cycle_features,
                'skeleton_data': self.skeleton_data
            }
            
            # 添加到工况列表
            self.workcase_data.append(workcase)
            
            return True, f"成功添加工况: {name}"
        
        except Exception as e:
            logger.error(f"添加工况出错: {str(e)}")
            return False, f"添加工况过程中发生错误: {str(e)}"
    
    def clear_workcases(self):
        """清空工况列表
        
        返回:
            tuple: (success, message)
        """
        self.workcase_data = []
        return True, "已清空工况数据"
    
    def generate_multi_workcase_skeleton_curve(self, displacement_threshold=0.001):
        """从多个工况数据生成综合骨架曲线
        
        参数:
            displacement_threshold: 位移差值阈值，小于此值的点会被视为重复点
            
        返回:
            tuple: (success, skeleton_data, message)
        """
        try:
            # 1. 前置条件检查：需要至少两个工况数据
            if len(self.workcase_data) < 2:
                return False, None, "至少需要两个工况数据才能生成综合骨架曲线"
            
            # 记录详细的工况数据信息
            logging.info(f"开始生成多工况骨架曲线，工况数量: {len(self.workcase_data)}")
            
            # 2. 收集所有工况的峰值点
            all_skeleton_points = []
            
            # 添加原点作为基准点
            all_skeleton_points.append((0.0, 0.0))
            logging.info("添加原点(0.0, 0.0)作为基准点")
            
            # 遍历所有工况数据
            for i, workcase in enumerate(self.workcase_data):
                workcase_name = workcase.get('name', f"工况 {i+1}")
                logging.info(f"处理工况 {i+1}: {workcase_name}")
                
                # 检查工况数据是否有效
                if not workcase.get('cycle_features'):
                    logging.warning(f"工况 {workcase_name} 没有特征点数据，已跳过")
                    continue
                
                # 从工况的循环特征中提取峰值点
                workcase_points = []
                for cycle_num, features in workcase['cycle_features'].items():
                    # 添加正向峰值点
                    if 'positive_peak' in features and features['positive_peak'] is not None:
                        if not features.get('anomaly', False):  # 排除标记为异常的点
                            pos_peak = features['positive_peak']
                            workcase_points.append(pos_peak)
                            logging.info(f"  添加正峰值点: 循环{cycle_num}, 坐标{pos_peak}")
                    
                    # 添加负向峰值点
                    if 'negative_peak' in features and features['negative_peak'] is not None:
                        if not features.get('anomaly', False):  # 排除标记为异常的点
                            neg_peak = features['negative_peak']
                            workcase_points.append(neg_peak)
                            logging.info(f"  添加负峰值点: 循环{cycle_num}, 坐标{neg_peak}")
                
                logging.info(f"工况 {workcase_name} 提取了 {len(workcase_points)} 个特征点")
                all_skeleton_points.extend(workcase_points)
            
            # 3. 点集处理
            logging.info(f"总共收集到 {len(all_skeleton_points)} 个特征点")
            # 按照位移值从小到大排序所有峰值点
            all_skeleton_points.sort(key=lambda p: p[0])
            
            # 去除重复和过于接近的点
            filtered_points = []
            for point in all_skeleton_points:
                # 检查是否与已添加的点过于接近
                is_close = False
                for existing_point in filtered_points:
                    if abs(point[0] - existing_point[0]) < displacement_threshold:
                        is_close = True
                        logging.info(f"过滤接近点: {point} 接近于 {existing_point}")
                        break
                
                if not is_close:
                    filtered_points.append(point)
            
            logging.info(f"过滤后剩余 {len(filtered_points)} 个特征点")
            
            # 4. 生成骨架曲线
            # 检查是否有足够的点生成骨架曲线
            if len(filtered_points) >= 2:
                skeleton_disp, skeleton_force = zip(*filtered_points)
                logging.info(f"生成的骨架曲线位移值: {skeleton_disp}")
                logging.info(f"生成的骨架曲线力值: {skeleton_force}")
                skeleton_data = (np.array(skeleton_disp), np.array(skeleton_force))
                self.skeleton_data = skeleton_data  # 更新类的骨架曲线数据
                return True, skeleton_data, "成功生成多工况综合骨架曲线"
            else:
                return False, None, "点数不足，无法生成有效的骨架曲线"
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, None, f"生成多工况骨架曲线过程中发生错误: {str(e)}"
            
    def add_current_as_workcase(self):
        """将当前处理的数据添加为工况
        
        返回:
            tuple: (success, message)
        """
        try:
            import copy
            
            # 检查是否有处理过的数据
            if self.processed_data is None:
                return False, "没有处理过的数据可添加"
                
            # 检查是否有循环数据
            if self.cycles is None or len(self.cycles) == 0:
                return False, "当前数据没有识别出循环"
                
            # 如果没有特征点数据，尝试生成
            if self.cycle_features is None:
                self.analyze_cycle_features()
                
            # 创建工况名称
            file_name = os.path.basename(self.file_path) if self.file_path else None
            name = f"工况 {len(self.workcase_data) + 1}"
            if file_name:
                name = f"{name} ({file_name})"
                
            # 记录当前参数
            current_parameters = {}
            if hasattr(self, 'params'):
                current_parameters = copy.deepcopy(self.params)
            
            # 创建工况数据(深拷贝，避免后续修改影响已保存的工况)
            workcase = {
                'name': name,
                'file_name': file_name,
                'file_path': self.file_path,
                'processed_data': copy.deepcopy(self.processed_data),
                'cycles': copy.deepcopy(self.cycles),
                'cycle_features': copy.deepcopy(self.cycle_features),
                'parameters': current_parameters
            }
            
            # 添加到工况数据列表
            self.workcase_data.append(workcase)
            
            logging.info(f"成功添加工况: {name}, 当前工况总数: {len(self.workcase_data)}")
            
            return True, f"已添加工况: {name}\n当前工况总数: {len(self.workcase_data)}"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"添加工况过程中发生错误: {str(e)}"
            
    def clear_workcase_data(self):
        """清空工况数据"""
        self.workcase_data = []