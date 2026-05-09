# 标炬（LabelTorch）打包与分发规划

## 交付物

1. `labeltorch-windows-cpu.zip`
2. `labeltorch-windows-cuda121.zip`

## 打包原则

1. 解压即用
2. 内置运行时与依赖
3. 首次启动执行环境自检

## 包内容

1. 主程序可执行文件
2. Python runtime
3. 必需模型依赖
4. 配置模板
5. 日志目录

## 启动自检项

1. 可写目录检查
2. SQLite 初始化检查
3. CUDA 可用性检查（CUDA 包）
4. 回退 CPU 训练提示
