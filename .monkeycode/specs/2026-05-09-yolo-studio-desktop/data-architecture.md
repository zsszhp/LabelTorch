# 标炬（LabelTorch）数据架构

## 数据分类

1. 元数据：SQLite
2. 原始数据：图片与标签文件
3. 训练产物：weights/logs/metrics
4. 导出产物：pt/onnx

## 元数据主表

1. projects
2. datasets
3. dataset_samples
4. class_mappings
5. train_jobs
6. model_versions
7. annotation_changes
8. export_tasks

## 数据一致性规则

1. class_mappings 更新必须触发标签重写任务。
2. train_jobs 创建后配置快照不可修改。
3. model_versions 与 train_jobs 一对一关联。
4. annotation_changes 必须记录操作者动作链（单用户也要审计）。

## 存储路径约束

1. 所有项目文件必须落在 project root。
2. 训练与导出目录按 version_id 隔离。
3. 临时文件统一放在 `.cache` 并周期清理。
