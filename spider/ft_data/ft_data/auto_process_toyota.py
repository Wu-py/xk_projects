import os
import zipfile
import subprocess
import shutil
import time
import sys
import locale

# ================= 配置区域 =================
SOURCE_DIR = r"D:\新款海外版（丰田）"
EXTRACT_ROOT = r"D:\ft_data"
SPIDER_SCRIPT = r"D:\projects\xk_projects\spider\ft_data\ft_data\run_2.py"
HTTP_PORT = 8000


# ===========================================

def get_zip_files(directory):
    """获取目录下所有的 zip 文件"""
    if not os.path.exists(directory):
        print(f"错误：源目录不存在 - {directory}")
        return []

    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith('.zip')]
    return sorted(files)[:2]


def extract_zip(zip_path, extract_to):
    """解压 zip 文件"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"[成功] 已解压: {os.path.basename(zip_path)}")
        return True
    except Exception as e:
        print(f"[失败] 解压出错: {e}")
        return False


def get_target_directory_v3(base_path):
    """获取第一层目录作为目标目录"""
    try:
        items = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

        if not items:
            print("[错误] 解压后未找到任何文件夹。")
            return None

        target_dir = os.path.join(base_path, items[0])
        print(f"  [定位] 目标工作目录 (第一层): {os.path.basename(target_dir)}")
        print(f"  [路径]: {target_dir}")

        return target_dir

    except Exception as e:
        print(f"[异常] 获取目录失败: {e}")
        return None


def run_process(work_dir, folder_name):
    """启动服务器 -> 运行脚本 -> 关闭服务器 (已修复编码问题)"""
    http_proc = None
    try:
        # 1. 启动 HTTP Server
        print(f"[启动] HTTP Server (端口 {HTTP_PORT}) @ {work_dir}")

        # 创建独立的环境变量副本，设置 Python 输出编码为 UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        http_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(HTTP_PORT)],
            cwd=work_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env
        )
        time.sleep(2)

        if http_proc.poll() is not None:
            raise Exception("HTTP Server 启动失败")

        # 2. 运行爬虫脚本
        print(f"[执行] 运行脚本: {os.path.basename(SPIDER_SCRIPT)}, 参数: {folder_name}")

        # 关键修复：
        # encoding='utf-8': 强制使用 UTF-8 解码输出
        # errors='ignore': 如果遇到无法解码的字符，直接忽略，防止崩溃
        result = subprocess.run(
            [sys.executable, SPIDER_SCRIPT, folder_name],
            cwd=os.path.dirname(SPIDER_SCRIPT),
            # capture_output=True,
            # text=True,
            # encoding='utf-8',
            # errors='ignore',
            env=env,
            timeout=1800  # 可选：设置超时时间，防止脚本卡死 (单位秒)
        )

        if result.returncode == 0:
            print("[完成] 脚本执行成功。")
        else:
            print(f"[警告] 脚本执行结束 (返回码:{result.returncode})。")
            if result.stderr:
                err_msg = result.stderr.strip()
                if len(err_msg) > 300:
                    err_msg = err_msg[:300] + "... (日志过长已截断)"
                print(f"       错误详情: {err_msg}")

        return True
    except subprocess.TimeoutExpired:
        print("[错误] 脚本执行超时！")
        return False
    except Exception as e:
        print(f"[错误] 执行过程异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 3. 关闭 HTTP Server
        if http_proc:
            print("[停止] 正在关闭 HTTP Server...")
            http_proc.terminate()
            try:
                http_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                http_proc.kill()
            print("[停止] HTTP Server 已关闭。")


def main():
    print("=" * 60)
    print("开始批量处理 (逻辑：第一层目录即为目标 | 编码优化版)")
    print("=" * 60)

    os.makedirs(EXTRACT_ROOT, exist_ok=True)

    zip_files = get_zip_files(SOURCE_DIR)

    if not zip_files:
        print("未找到 zip 文件。")
        return

    print(f"发现 {len(zip_files)} 个文件，开始处理...\n")

    for i, zip_file in enumerate(zip_files, 1):
        print(f"\n--- [{i}/{len(zip_files)}] {os.path.basename(zip_file)} ---")

        if not extract_zip(zip_file, EXTRACT_ROOT):
            continue

        target_dir = get_target_directory_v3(EXTRACT_ROOT)

        if not target_dir:
            print("[跳过] 无法定位目标目录。")
            continue

        folder_name = os.path.basename(target_dir)

        run_process(target_dir, folder_name)

        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
                print(f"[清理] 已删除目录: {os.path.basename(target_dir)}")
            except Exception as e:
                print(f"[错误] 删除目录失败: {e}")
        else:
            print("[提示] 目录已被删除或不存在，跳过清理。")

    print("\n" + "=" * 60)
    print("全部处理完毕！")
    print("=" * 60)


if __name__ == "__main__":
    # 设置全局默认编码为 UTF-8 (针对部分旧版 Python 环境)
    # 注意：这在某些系统上可能需要重启终端才生效，但在 subprocess 中我们已通过 env 控制
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass

    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断程序。")
    except Exception as e:
        print(f"\n程序发生严重错误: {e}")
        import traceback

        traceback.print_exc()