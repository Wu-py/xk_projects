# run_2.py
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import os


def run_crawler_subprocess(directory):
    # 调用独立的 worker.py 脚本
    # sys.executable 确保使用当前相同的 Python 解释器
    cmd = [sys.executable, 'worker.py', directory, 'ft_ewd']

    try:
        # 运行子进程，等待完成
        result = subprocess.run(cmd, check=False)  # check=False 允许我们处理非零退出码
        if result.returncode == 0:
            print(f"✅ {directory} 完成")
            return True
        else:
            print(f"❌ {directory} 失败，退出码: {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ {directory} 异常: {e}")
        return False


if __name__ == '__main__':
    directories = ['N0037', 'N0038']
    MAX_CONCURRENT = 1  # 控制同时运行的 subprocess 数量

    print(f"开始运行，总任务数: {len(directories)}, 最大并发数: {MAX_CONCURRENT}")

    with ProcessPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        future_to_dir = {executor.submit(run_crawler_subprocess, d): d for d in directories}

        for future in as_completed(future_to_dir):
            # 这里只是接收结果，具体的打印在子函数里做了，也可以在这里统一处理
            pass

    print("所有任务调度结束。")