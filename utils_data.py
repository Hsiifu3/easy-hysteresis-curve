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

# ==================== 数据读取与预处理函数 ====================

def read_excel_data(file_path, skiprows=0):
    """读取Excel数据文件
    
    参数:
        file_path (str): Excel文件路径
        skiprows (int): 要跳过的数据行数(不包括列标题行)
    
    返回:
        tuple: (DataFrame, error_message)
    """
    try:
        # 根据文件扩展名选择合适的引擎
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.xls':
            engine = 'xlrd'
            logger.info(f"检测到.xls文件，使用xlrd引擎: {file_path}")
            
            # 仅对.xls文件尝试检测特殊格式
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_lines = [f.readline().strip() for _ in range(min(5, skiprows + 2))]
                
                # 检查文件是否可能是固定宽度或特殊格式的文本文件
                first_line_content = first_lines[0] if first_lines else ""
                
                # 更严格的特殊格式检测条件，必须包含特定模式才识别为特殊文本
                is_special_text_format = False
                if first_line_content and ('_' in first_line_content and any(c.isdigit() for c in first_line_content)):
                    is_special_text_format = True
                    logger.info(f"检测到可能是特殊格式的文本文件: {file_path}")
                
                # 如果检测到特殊格式，直接尝试使用文本解析方法
                if is_special_text_format:
                    return parse_special_text_file(file_path, skiprows)
            except Exception as text_check_error:
                logger.warning(f"检查文件格式时出错: {str(text_check_error)}")
            
        elif file_ext == '.xlsx':
            engine = 'openpyxl'
            logger.info(f"检测到.xlsx文件，使用openpyxl引擎: {file_path}")
            # 对于.xlsx文件，直接使用Excel引擎读取，不检测特殊格式
        else:
            # 对于其他扩展名或未知扩展名，让pandas自动选择
            engine = None
            logger.info(f"未知文件类型，使用默认引擎: {file_path}")
        
        try:
            # 尝试使用Excel引擎读取
            # 总是读取第一行作为列标题，使用header=0
            # 如果skiprows>0，则跳过数据中的前skiprows行
            if skiprows > 0:
                # 读取列标题，指定引擎
                header_df = pd.read_excel(file_path, nrows=1, engine=engine)
                # 读取数据，跳过指定的行数(包括标题行)，指定引擎
                data_df = pd.read_excel(file_path, skiprows=skiprows+1, engine=engine)
                # 确保数据使用与标题行相同的列名
                data_df.columns = header_df.columns
                return data_df, None
            else:
                # 如果不需要跳过行，直接读取文件，指定引擎
                data = pd.read_excel(file_path, engine=engine)
                return data, None
                
        except Exception as excel_error:
            # 如果使用Excel引擎读取失败，尝试使用CSV格式读取
            logger.warning(f"使用Excel引擎读取失败: {str(excel_error)}，尝试使用CSV格式读取")
            
            # 尝试不同的分隔符
            separators = [',', '\t', ';', ' ']
            for sep in separators:
                try:
                    if skiprows > 0:
                        # 读取标题行
                        header_df = pd.read_csv(file_path, nrows=1, sep=sep, encoding='utf-8', on_bad_lines='skip')
                        # 读取数据行，跳过指定行数
                        data_df = pd.read_csv(file_path, skiprows=skiprows+1, sep=sep, encoding='utf-8', on_bad_lines='skip')
                        # 使用标题行的列名
                        data_df.columns = header_df.columns
                        logger.info(f"成功使用CSV格式读取文件，分隔符为: '{sep}'")
                        return data_df, None
                    else:
                        data = pd.read_csv(file_path, sep=sep, encoding='utf-8', on_bad_lines='skip')
                        logger.info(f"成功使用CSV格式读取文件，分隔符为: '{sep}'")
                        return data, None
                except Exception as csv_error:
                    continue  # 尝试下一个分隔符
            
            # 如果所有尝试都失败，尝试使用固定宽度格式读取
            try:
                logger.info("尝试使用固定宽度格式读取文件")
                if skiprows > 0:
                    # 先读取一行来确定列名
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        header_line = f.readline().strip()
                    
                    # 以空格分隔列名
                    columns = header_line.split()
                    
                    # 读取数据，跳过前skiprows+1行
                    data = pd.read_fwf(file_path, skiprows=skiprows+1, encoding='utf-8')
                    
                    # 如果列数不匹配，手动设置列名
                    if len(columns) == len(data.columns):
                        data.columns = columns
                        
                    return data, None
                else:
                    data = pd.read_fwf(file_path, encoding='utf-8') 
                    return data, None
            except Exception as fwf_error:
                # 只有.xls文件才尝试使用特殊解析方法
                if file_ext == '.xls':
                    return parse_special_text_file(file_path, skiprows)
                else:
                    # 其他文件直接返回错误
                    return None, f"所有读取方法均失败。Excel错误: {str(excel_error)}"
                
    except Exception as e:
        logger.error(f"读取文件出错: {str(e)}")
        return None, str(e)

def parse_special_text_file(file_path, skiprows=0):
    """
    解析特殊格式的文本文件，如固定宽度但不符合标准格式的文件
    
    参数:
        file_path (str): 文件路径
        skiprows (int): 要跳过的行数
        
    返回:
        tuple: (DataFrame, error_message)
    """
    try:
        logger.info(f"使用特殊解析方法读取文件: {file_path}")
        
        # 读取整个文件内容
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        if len(lines) <= skiprows:
            return None, "文件行数少于跳过的行数"
            
        # 提取标题行和数据行
        header_line = lines[0].strip() if lines else ""
        data_lines = lines[skiprows+1:] if skiprows > 0 else lines[1:]
        
        # 尝试分析文件格式
        # 1. 检查第一行是否包含可能的标题
        if "_" in header_line or header_line.replace("_", "").isdigit():
            # 可能是数据行而不是标题行，尝试推断列数
            sample_lines = data_lines[:min(10, len(data_lines))]
            
            # 分析行长度和可能的分隔符
            line_lengths = [len(line.strip()) for line in sample_lines if line.strip()]
            avg_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0
            
            # 检查数字与空格模式
            patterns = []
            for line in sample_lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 识别数字块和空格块
                current_type = 'digit' if line[0].isdigit() or line[0] == '-' or line[0] == '.' else 'space'
                start_idx = 0
                blocks = []
                
                for i, char in enumerate(line):
                    is_digit_char = char.isdigit() or char == '-' or char == '.'
                    new_type = 'digit' if is_digit_char else 'space'
                    
                    if new_type != current_type:
                        blocks.append((current_type, start_idx, i-1))
                        current_type = new_type
                        start_idx = i
                        
                # 添加最后一个块
                blocks.append((current_type, start_idx, len(line)-1))
                
                # 只保留数字块
                digit_blocks = [block for block in blocks if block[0] == 'digit']
                patterns.append(digit_blocks)
            
            # 分析模式，找出一致的列宽
            column_positions = []
            if patterns:
                max_cols = max(len(p) for p in patterns)
                for col_idx in range(max_cols):
                    start_positions = []
                    end_positions = []
                    for p in patterns:
                        if col_idx < len(p):
                            start_positions.append(p[col_idx][1])
                            end_positions.append(p[col_idx][2])
                    
                    if start_positions and end_positions:
                        # 使用众数或平均值
                        start_pos = int(sum(start_positions) / len(start_positions))
                        end_pos = int(sum(end_positions) / len(end_positions))
                        column_positions.append((start_pos, end_pos))
            
            # 如果无法识别模式，使用简单的空格分隔
            if not column_positions:
                # 使用空格分隔
                data_rows = []
                for line in data_lines:
                    line = line.strip()
                    if line:
                        values = line.split()
                        data_rows.append(values)
                
                # 确定列数
                if data_rows:
                    col_count = max(len(row) for row in data_rows)
                    # 生成默认列名
                    columns = [f"Column_{i+1}" for i in range(col_count)]
                    
                    # 处理数据，确保每行列数一致
                    normalized_data = []
                    for row in data_rows:
                        if len(row) < col_count:
                            row.extend([None] * (col_count - len(row)))
                        normalized_data.append(row)
                    
                    # 创建DataFrame
                    df = pd.DataFrame(normalized_data, columns=columns)
                    
                    # 尝试将所有列转换为数值
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    
                    return df, None
            else:
                # 使用识别出的列位置解析数据
                data_rows = []
                for line in data_lines:
                    if not line.strip():
                        continue
                        
                    row_values = []
                    for start, end in column_positions:
                        if start < len(line) and end < len(line):
                            value = line[start:end+1].strip()
                            row_values.append(value)
                        else:
                            row_values.append(None)
                    
                    data_rows.append(row_values)
                
                if data_rows:
                    # 生成默认列名
                    columns = [f"Column_{i+1}" for i in range(len(column_positions))]
                    
                    # 创建DataFrame
                    df = pd.DataFrame(data_rows, columns=columns)
                    
                    # 尝试将所有列转换为数值
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    
                    return df, None
        
        # 2. 如果上述方法失败，尝试直接按行解析
        data_rows = []
        for line in data_lines:
            line = line.strip()
            if line:
                # 尝试将行分割为若干部分
                parts = line.split()
                if parts:
                    data_rows.append(parts)
        
        if data_rows:
            # 确定最大列数
            max_cols = max(len(row) for row in data_rows)
            
            # 生成默认列名
            columns = [f"Column_{i+1}" for i in range(max_cols)]
            
            # 处理数据，确保每行列数一致
            normalized_data = []
            for row in data_rows:
                if len(row) < max_cols:
                    row.extend([None] * (max_cols - len(row)))
                normalized_data.append(row)
            
            # 创建DataFrame
            df = pd.DataFrame(normalized_data, columns=columns)
            
            # 尝试将所有列转换为数值
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            
            return df, None
            
        # 如果所有尝试都失败
        return None, "无法解析特殊格式的文本文件"
        
    except Exception as e:
        logger.error(f"特殊文本文件解析失败: {str(e)}")
        return None, f"特殊文本文件解析失败: {str(e)}"

def extract_channel_data(data, disp_channel, force1_channel, force2_channel=None):
    """提取特定通道的数据，并转换为数值类型
    
    参数:
        data (DataFrame): 数据表
        disp_channel (str): 位移通道名称
        force1_channel (str): 第一个力传感器通道名称
        force2_channel (str): 第二个力传感器通道名称(可选)
        
    返回:
        tuple: (displacement, total_force, error_message)
    """
    try:
        # 确保数据为数值类型，并处理可能的NaN值
        if disp_channel not in data.columns:
            return None, None, f"位移通道 '{disp_channel}' 不存在"
        
        if force1_channel not in data.columns:
            return None, None, f"力传感器通道1 '{force1_channel}' 不存在"
        
        displacement = pd.to_numeric(data[disp_channel], errors='coerce').values
        
        # 提取力数据
        force1 = pd.to_numeric(data[force1_channel], errors='coerce').values
        
        # 计算合力
        if force2_channel and force2_channel in data.columns:
            force2 = pd.to_numeric(data[force2_channel], errors='coerce').values
            total_force = force1 + force2
        else:
            total_force = force1
        
        # 处理NaN值
        displacement = np.nan_to_num(displacement, nan=0.0, posinf=0.0, neginf=0.0)
        total_force = np.nan_to_num(total_force, nan=0.0, posinf=0.0, neginf=0.0)
            
        return displacement, total_force, None
    except Exception as e:
        return None, None, str(e)

def preprocess_data(displacement, force, sampling_rate=None):
    """数据预处理: 应用滑动平均滤波并消除传感器零漂
    
    参数:
        displacement (ndarray): 位移数据
        force (ndarray): 力数据
        sampling_rate (float): 采样率(Hz)，用于计算循环持续时间
        
    返回:
        tuple: (processed_displacement, processed_force, error_message)
    """
    try:
        # 替换可能的无穷大值和NaN值
        displacement = np.nan_to_num(displacement, nan=0.0, posinf=0.0, neginf=0.0)
        force = np.nan_to_num(force, nan=0.0, posinf=0.0, neginf=0.0)
        
        # 1. 应用滑动平均滤波 (窗口长度=5)
        displacement_filtered = uniform_filter1d(displacement, size=5)
        force_filtered = uniform_filter1d(force, size=5)
        
        # 2. 消除传感器零漂（取前10个采样点的均值作为基准）
        if len(displacement_filtered) >= 10 and len(force_filtered) >= 10:
            disp_zero_drift = np.mean(displacement_filtered[:10])
            force_zero_drift = np.mean(force_filtered[:10])
            
            displacement_corrected = displacement_filtered - disp_zero_drift
            force_corrected = force_filtered - force_zero_drift
        else:
            displacement_corrected = displacement_filtered
            force_corrected = force_filtered
            
        return displacement_corrected, force_corrected, None
    except Exception as e:
        return displacement, force, f"数据预处理错误: {str(e)}"