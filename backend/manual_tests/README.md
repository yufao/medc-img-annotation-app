该目录用于存放手工/半自动测试脚本（不会被 pytest 自动收集执行）。

包含示例：
- test_annotation.py：直接向 Mongo 写入一条标注以验证自增序列。
- test_export.py：演练导出到 xlsx 并打印工作表信息。
- test_user_independent_progress.py：调用运行中后端接口验证“用户独立进度”。

注意：这些脚本可能依赖运行中的服务或真实数据库连接，请在本地验证时谨慎使用。
