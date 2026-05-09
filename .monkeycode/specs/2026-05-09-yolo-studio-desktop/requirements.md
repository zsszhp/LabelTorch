# Requirements Document

## Introduction

本项目是一个面向工业缺陷检测场景的本地离线桌面软件。目标是降低 YOLO 数据导入、训练配置、版本迭代、辅助标注与模型导出的操作复杂度，减少人工流程错误。

## Glossary

- System: 桌面软件本体
- Dataset: 用户导入的数据集（图片与标签）
- Model Version: 一次完整训练产生的模型版本
- Assisted Annotation: 使用历史模型推理结果辅助人工确认与修正标注
- Incremental Training: 基于上一版权重继续训练新数据版本

## Requirements

### Requirement 1: 离线桌面运行

**User Story:** AS 工业算法工程师, I want 软件可在 Windows 本地离线运行, so that 我无需依赖云端环境并可稳定使用 GPU 训练。

#### Acceptance Criteria

1. WHEN 用户启动软件, the System SHALL 在无网络连接条件下完成核心功能使用。
2. WHILE 软件运行于 Windows, the System SHALL 支持 CPU 训练与 NVIDIA CUDA 训练模式选择。
3. IF 用户机器缺少 Python 或训练依赖, the System SHALL 通过绿色包内置运行时完成启动与训练任务。
4. IF 训练运行异常, the System SHALL 记录错误日志并保持主界面可响应。

### Requirement 2: 数据集导入与管理

**User Story:** AS 工业算法工程师, I want 导入图片与 YOLO txt 标签, so that 我可以快速构建训练任务。

#### Acceptance Criteria

1. WHEN 用户选择数据集目录, the System SHALL 校验图片与 YOLO txt 标签的完整性并输出校验报告。
2. IF 发现缺失标签或非法坐标, the System SHALL 标记异常样本并允许用户继续处理其余样本。
3. WHILE 用户浏览样本, the System SHALL 显示图片、标注框与类别信息。
4. WHEN 用户设置训练集与验证集比例, the System SHALL 生成可复用的数据划分配置。

### Requirement 3: 模型训练配置与执行

**User Story:** AS 工业算法工程师, I want 选择 YOLO 模型族并配置关键参数, so that 我可以稳定执行训练。

#### Acceptance Criteria

1. WHEN 用户新建训练任务, the System SHALL 提供 yolov5、yolov8、yolov8_obb、yolov10、yolov11 的可选项。
2. WHEN 用户配置训练参数, the System SHALL 支持 img_size、batch、epochs、patience、device、workers、project、name。
3. WHILE 任务执行中, the System SHALL 实时显示日志、epoch 进度、关键指标与剩余时间估计。
4. IF 用户启用早停, the System SHALL 使用 mAP50-95 相关指标驱动 patience 逻辑且默认 patience=50。
5. IF 训练中断, the System SHALL 保存任务状态并提示是否在后续版本使用断点续训能力。

### Requirement 4: 模型版本管理与增量训练

**User Story:** AS 工业算法工程师, I want 管理多版本模型并选择历史权重增量训练, so that 我可以持续提升模型效果。

#### Acceptance Criteria

1. WHEN 一次训练完成, the System SHALL 生成独立 Model Version 记录并关联参数、数据集快照与指标。
2. WHEN 用户创建新版本训练任务, the System SHALL 允许选择上一版权重作为初始化模型。
3. WHILE 用户查看版本列表, the System SHALL 展示版本号、创建时间、核心指标与导出产物状态。

### Requirement 5: 辅助标注与人工修正

**User Story:** AS 工业算法工程师, I want 使用历史模型生成候选框并进行人工修正, so that 我可以更快完成新增数据标注。

#### Acceptance Criteria

1. WHEN 用户选择历史模型执行辅助标注, the System SHALL 生成候选框并附带类别与置信度。
2. WHEN 用户设置置信度阈值, the System SHALL 仅显示满足阈值的候选框。
3. WHILE 用户审核候选框, the System SHALL 支持框体拖拽调整、删除框、修改类别、补充拉框。
4. WHEN 用户批量确认候选框, the System SHALL 将确认结果写回标签文件并保留操作记录。

### Requirement 6: 模型导出

**User Story:** AS 工业算法工程师, I want 导出训练结果为 pt 与 onnx, so that 我可以用于不同部署场景。

#### Acceptance Criteria

1. WHEN 用户在版本详情中执行导出, the System SHALL 支持 pt 与 onnx 导出。
2. WHEN 用户导出 onnx, the System SHALL 提供 opset、dynamic、simplify 参数并给出行业常用默认值。
3. IF 导出失败, the System SHALL 返回可定位原因的错误信息并保留失败日志。

### Requirement 7: 稳定性与可用性

**User Story:** AS 工业算法工程师, I want 软件在大规模样本下稳定运行, so that 我可以避免闪退和流程中断。

#### Acceptance Criteria

1. WHILE 数据规模在 100 到 10000 张区间, the System SHALL 保持界面可操作并避免无响应崩溃。
2. IF 任一后台任务异常, the System SHALL 隔离异常并不导致主进程退出。
3. WHEN 软件异常退出后再次启动, the System SHALL 能恢复最近项目元数据与任务历史。
