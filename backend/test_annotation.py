"""
已迁移至 backend/manual_tests/test_annotation.py
保留占位，防止 pytest 自动收集执行。
"""

if __name__ == "__main__":
    from pathlib import Path
    import runpy
    target = Path(__file__).with_name('manual_tests') / 'test_annotation.py'
    if target.exists():
        runpy.run_path(str(target))
    else:
        print("manual_tests/test_annotation.py 不存在")
