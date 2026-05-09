# 标炬（LabelTorch）文件架构与模块说明

## 1. 模块分层

1. UI Layer
   - 页面、组件、交互状态管理
2. Service Layer
   - 用例编排、任务调度、跨模块事务
3. Domain Layer
   - Project/Dataset/TrainJob/ModelVersion 等核心实体
4. Infra Layer
   - SQLite、文件系统、Ultralytics 执行器、导出器

## 2. 推荐文件结构

```text
app/
  ui/
    pages/
      project_page.py
      dataset_page.py
      train_page.py
      annotation_page.py
      export_page.py
    widgets/
      image_canvas.py
      class_mapping_table.py
      train_log_panel.py
  services/
    project_service.py
    dataset_service.py
    annotation_service.py
    training_service.py
    version_service.py
    export_service.py
  domain/
    models.py
    enums.py
    schemas.py
  infra/
    db/
      sqlite.py
      migrations/
    storage/
      file_repo.py
    ml/
      ultralytics_runner.py
      onnx_exporter.py
    logging/
      logger.py
  tasks/
    task_manager.py
    worker_process.py
```

## 3. 数据目录约定

```text
<project_root>/
  datasets/
    <dataset_name>/
      images/
      labels/
      splits/
  models/
    <version_id>/
      weights/
      metrics/
      logs/
  exports/
    <version_id>/
      model.pt
      model.onnx
```

## 4. 关键设计约束

1. 训练输出按 version_id 隔离目录。
2. 标签改写先写临时文件再原子替换。
3. UI 不直接调用 Ultralytics，必须经 Service 层。
