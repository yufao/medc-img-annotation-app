# 测试说明

当前测试文件分散在仓库根目录与 backend/tests/ 中。

建议统一迁移至 tests/ 目录，并使用 pytest 的默认发现规则：
- 统一命名为 test_*.py
- 根目录配置 pytest.ini 或 pyproject.toml 指定测试路径

暂未物理移动文件（避免影响你本机脚本/CI），待你确认后我再执行批量迁移与清理。
