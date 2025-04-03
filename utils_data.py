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
                    
                    # 尝试转换为数值型
                    for col in df.columns:
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        except:
                            pass
                            
                    return df, None
            else:
                # 使用识别出的列位置解析数据
                data_rows = []
                for line in data_lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # 提取每列的数据
                    row_values = []
                    for start_pos, end_pos in column_positions:
                        if start_pos >= len(line):
                            value = None
                        else:
                            end_pos = min(end_pos, len(line) - 1)
                            value = line[start_pos:end_pos+1].strip()
                        row_values.append(value)
                        
                    data_rows.append(row_values)
                
                # 生成默认列名
                columns = [f"Column_{i+1}" for i in range(len(column_positions))]
                
                # 创建DataFrame
                df = pd.DataFrame(data_rows, columns=columns)
                
                # 尝试转换为数值型
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass
                        
                return df, None
        else:
            # 假设第一行是标题行，使用空格分隔
            columns = header_line.split()
            
            # 如果没有足够的列名，生成默认列名
            if not columns:
                # 尝试确定列数
                sample_line = data_lines[0].strip() if data_lines else ""
                col_count = len(sample_line.split())
                columns = [f"Column_{i+1}" for i in range(col_count)]
            
            # 读取数据行
            data_rows = []
            for line in data_lines:
                line = line.strip()
                if line:
                    values = line.split()
                    data_rows.append(values)
            
            # 确保所有行的列数一致
            col_count = len(columns)
            normalized_data = []
            for row in data_rows:
                if len(row) < col_count:
                    row.extend([None] * (col_count - len(row)))
                elif len(row) > col_count:
                    row = row[:col_count]
                normalized_data.append(row)
            
            # 创建DataFrame
            df = pd.DataFrame(normalized_data, columns=columns)
            
            # 尝试转换为数值型
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass
                    
            return df, None
            
    except Exception as e:
        logger.error(f"解析特殊格式文件出错: {str(e)}")
        return None, f"解析特殊格式文件出错: {str(e)}"

# ==================== 数据预处理函数 ====================

def correct_baseline(disp, force):
    """基线校正，消除系统偏移或飘移
    
    参数:
        disp: 位移数据
        force: 力数据
        
    返回:
        tuple: (corrected_disp, corrected_force)
    """
    if len(disp) == 0 or len(force) == 0:
        return disp, force
        
    # 使用线性拟合校正基线
    x = np.arange(len(disp))
    
    # 拟合位移基线
    disp_baseline = np.polyfit(x, disp, 1)
    disp_corrected = disp - np.polyval(disp_baseline, x)
    
    # 拟合力基线
    force_baseline = np.polyfit(x, force, 1)
    force_corrected = force - np.polyval(force_baseline, x)
    
    return disp_corrected, force_corrected

def zero_baseline(disp, force):
    """零点校正，确保初始点在原点附近
    
    参数:
        disp: 位移数据
        force: 力数据
        
    返回:
        tuple: (zeroed_disp, zeroed_force)
    """
    if len(disp) == 0 or len(force) == 0:
        return disp, force
        
    # 计算前10%数据的平均值作为零点偏移
    n_samples = max(1, int(len(disp) * 0.1))
    
    disp_offset = np.mean(disp[:n_samples])
    force_offset = np.mean(force[:n_samples])
    
    return disp - disp_offset, force - force_offset

def remove_outliers(disp, force, threshold=3.0):
    """移除异常值
    
    参数:
        disp: 位移数据
        force: 力数据
        threshold: 标准差倍数阈值
        
    返回:
        tuple: (filtered_disp, filtered_force)
    """
    if len(disp) < 3 or len(force) < 3:
        return disp, force
        
    # 计算位移和力的标准差
    disp_std = np.std(disp)
    force_std = np.std(force)
    
    # 计算位移和力的均值
    disp_mean = np.mean(disp)
    force_mean = np.mean(force)
    
    # 创建一个掩码，标记非异常值
    mask = (
        (np.abs(disp - disp_mean) < threshold * disp_std) & 
        (np.abs(force - force_mean) < threshold * force_std)
    )
    
    # 如果掩码移除了太多数据，则保持原始数据
    if np.sum(mask) < len(disp) * 0.8:
        logger.warning(f"异常值过多，保留原始数据")
        return disp, force
    
    # 仅保留非异常数据
    return disp[mask], force[mask]

def smooth_data(disp, force, window=10):
    """平滑数据
    
    参数:
        disp: 位移数据
        force: 力数据
        window: 平滑窗口大小
        
    返回:
        tuple: (smoothed_disp, smoothed_force)
    """
    if len(disp) <= window or len(force) <= window:
        return disp, force
        
    # 使用移动平均平滑数据
    smoothed_disp = uniform_filter1d(disp, size=window)
    smoothed_force = uniform_filter1d(force, size=window)
    
    return smoothed_disp, smoothed_force

# ==================== 循环识别函数 ====================

def identify_loading_cycles(disp, force, prominence=0.1, min_points=100):
    """识别加载循环的峰谷值
    
    参数:
        disp: 位移数据
        force: 力数据
        prominence: 峰值识别突出度参数(0-1)
        min_points: 最小循环点数
        
    返回:
        tuple: (cycles, peaks, valleys)
    """
    try:
        # 适应信号范围的突出度值
        disp_range = np.max(disp) - np.min(disp)
        adapted_prominence = prominence * disp_range
        
        # 找出位移的峰值和谷值
        peaks, _ = find_peaks(disp, prominence=adapted_prominence)
        valleys, _ = find_peaks(-disp, prominence=adapted_prominence)
        
        # 确保有足够数量的峰谷值
        if len(peaks) == 0 or len(valleys) == 0:
            logger.warning("未识别到峰或谷，调整参数重试")
            # 降低突出度阈值重试
            return identify_loading_cycles(disp, force, prominence=prominence*0.5, min_points=min_points)
        
        # 排序所有极值点
        all_extremes = np.sort(np.concatenate([peaks, valleys]))
        
        # 初始化循环列表
        cycles = []
        
        for i in range(len(all_extremes) - 1):
            start_idx = all_extremes[i]
            end_idx = all_extremes[i + 1]
            
            # 检查循环点数是否足够
            if end_idx - start_idx >= min_points:
                cycles.append((start_idx, end_idx))
        
        logger.info(f"识别到 {len(cycles)} 个加载循环")
        return cycles, peaks, valleys
        
    except Exception as e:
        logger.error(f"识别加载循环出错: {str(e)}")
        return [], [], []

def calculate_cycle_features(cycles, disp, force):
    """计算每个循环的特征
    
    参数:
        cycles: 循环索引列表
        disp: 位移数据
        force: 力数据
        
    返回:
        list: 循环特征字典列表
    """
    features = []
    
    for start_idx, end_idx in cycles:
        cycle_disp = disp[start_idx:end_idx]
        cycle_force = force[start_idx:end_idx]
        
        # 计算特征
        feature = {
            "max_disp": np.max(cycle_disp),
            "min_disp": np.min(cycle_disp),
            "max_force": np.max(cycle_force),
            "min_force": np.min(cycle_force),
            "disp_range": np.max(cycle_disp) - np.min(cycle_disp),
            "force_range": np.max(cycle_force) - np.min(cycle_force),
            "start_idx": start_idx,
            "end_idx": end_idx,
            "length": end_idx - start_idx
        }
        
        features.append(feature)
    
    return features

# ==================== 分析函数 ====================

def calculate_stiffness_and_energy(disp, force):
    """计算刚度和能量耗散
    
    参数:
        disp: 位移数据
        force: 力数据
        
    返回:
        tuple: (stiffness, energy)
    """
    try:
        # 线性拟合计算刚度
        slope, _ = np.polyfit(disp, force, 1)
        
        # 计算闭合曲线包围的面积作为能量耗散
        energy = calculate_hysteresis_loop_area(disp, force)
        
        return slope, energy
        
    except Exception as e:
        logger.error(f"计算刚度和能量出错: {str(e)}")
        return 0, 0