# 准静态试验滞回曲线分析工具

本工具用于分析准静态试验的滞回曲线数据，实现滞回曲线的可视化、循环加载识别、等效刚度计算、骨架曲线生成等功能。

## 主要功能

- 数据读取与预处理：支持Excel格式的试验数据读取，可选择不同的数据通道
- 滞回曲线绘制：直观显示位移-力关系曲线
- 循环加载识别：自动识别试验中的加载循环
- 等效刚度计算：计算滞回曲线的等效刚度
- 骨架曲线生成：基于多个工况生成包络骨架曲线
- 批量处理：支持多个文件的批量处理和比较分析
- 结果导出：将分析结果导出为Excel文件

## 使用方法

1. 运行主程序 `python hysteresis_app.py`
2. 通过界面选择要分析的试验数据文件
3. 设置位移通道和力传感器通道
4. 点击"绘制滞回曲线"查看原始数据曲线
5. 点击"处理数据"进行数据预处理和循环识别
6. 点击"计算等效刚度"获取分析结果
7. 通过"添加当前工况"和"生成骨架曲线"进行多工况对比分析

## 程序结构

程序采用MVC架构设计，分为以下模块：

- **hysteresis_app.py**: 主程序入口，负责初始化和启动应用
- **hysteresis_gui.py**: 图形界面模块，包含所有UI组件创建和管理
- **hysteresis_data.py**: 数据处理模块，负责文件加载和数据分析
- **hysteresis_controller.py**: 控制器模块，连接GUI和数据处理逻辑
- **hysteresis_viz.py**: 可视化模块，负责图表绘制和结果展示
- **utils_data.py**: 数据处理工具函数模块
- **utils_visualization.py**: 可视化工具函数模块
- **utils_debug.py**: 调试工具模块

### 目录结构

```
准静态试验滞回曲线分析工具/
├── hysteresis_app.py         # 主程序入口
├── hysteresis_gui.py         # 图形界面模块
├── hysteresis_data.py        # 数据处理模块
├── hysteresis_controller.py  # 控制器模块
├── hysteresis_viz.py         # 可视化模块
├── utils_data.py             # 数据处理工具
├── utils_visualization.py    # 可视化工具
├── utils_debug.py            # 调试工具
├── logs/                     # 日志目录
├── tools/                    # 辅助工具脚本目录
│   ├── data-C.py             # 柱数据分析脚本
│   ├── data-S.py             # 墙数据分析脚本
│   └── to xlsx.py            # Excel格式转换脚本
└── README.md                 # 项目说明文档
```

## 依赖库

- numpy: 用于数值计算
- pandas: 用于数据处理
- matplotlib: 用于绘图
- scipy: 用于信号处理与科学计算
- tkinter: 用于图形界面

## 系统要求

- Python 3.6+
- Windows、Linux或macOS系统