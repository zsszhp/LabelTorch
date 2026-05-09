# 标炬（LabelTorch）工程任务书（可直接给 AI 编码）

## 1. 目录结构

```text
labeltorch/
  app/
    ui/
    services/
    domain/
    infra/
    tasks/
  runtime/
    python/
    cuda/
  scripts/
  tests/
  packaging/
```

## 2. 里程碑与任务

### M1 项目骨架

1. 初始化 PySide6 应用壳
2. 建立 SQLite 数据模型与迁移
3. 搭建日志系统与异常捕获

验收：可打开主界面并创建本地项目。

### M2 数据与标注

1. 实现 YOLO txt 导入器
2. 实现样本校验器
3. 实现类别抽取与 class 重映射
4. 实现 bbox 编辑器（增删改）

验收：导入后可完成编辑并正确回写标签文件。

### M3 训练与版本

1. 训练任务实体与状态机
2. Ultralytics 子进程执行器
3. 参数面板与早停控制
4. 训练结果入库为模型版本

验收：支持 v5/v8/v8_obb/v10/v11，训练完成自动生成版本。

### M4 辅助标注与增量训练

1. 历史模型推理接口
2. 置信度阈值筛选
3. 批量确认逻辑
4. 选择 parent version 权重继续训练

验收：可完成“老模型辅助新数据标注+增量训练”闭环。

### M5 导出与发布

1. pt/onnx 导出任务
2. ONNX 参数界面（opset/dynamic/simplify）
3. Windows CPU/CUDA 双包打包脚本
4. 启动自检与错误提示

验收：双包均可解压即用并完成导出。

## 3. 关键接口定义

```text
POST /project/create
POST /dataset/import
POST /dataset/remap-classes
POST /annotation/save
POST /train/create
POST /train/start
POST /train/stop
POST /assist/run
POST /assist/confirm-batch
POST /export/create
GET  /version/list
```

注：桌面端内部调用可实现为 Service API，不必真的暴露 HTTP。

## 4. 测试任务

1. 单元测试
   - YOLO 坐标合法性
   - 类别重映射一致性
   - 标注编辑回写正确性
2. 集成测试
   - 导入-训练-导出
   - 辅助标注-批量确认-增量训练
3. 稳定性测试
   - 10000 样本浏览与编辑稳定性

## 5. MVP 边界锁定

1. 不实现云端、权限、多人协作。
2. 不实现多格式双向转换。
3. 不实现多卡、超参搜索、实验看板。
