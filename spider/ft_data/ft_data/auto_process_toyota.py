import os
import zipfile
import subprocess
import shutil
import time
import sys

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
    return sorted(files)[:1]


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
    """
    【核心逻辑修正】
    直接获取第一层目录作为目标目录。
    逻辑：base_path -> [第一层目录 (目标)]
    """
    try:
        # 获取 base_path 下所有的子文件夹
        items = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

        if not items:
            print("[错误] 解压后未找到任何文件夹。")
            return None

        # 假设解压后只生成一个顶层文件夹，取第一个
        # 如果有多个，通常取最新创建的或按名称排序的第一个，这里取列表第一个
        target_dir = os.path.join(base_path, items[0])

        print(f"  [定位] 目标工作目录 (第一层): {os.path.basename(target_dir)}")
        print(f"  [路径]: {target_dir}")

        return target_dir

    except Exception as e:
        print(f"[异常] 获取目录失败: {e}")
        return None


def run_process(work_dir, folder_name):
    """启动服务器 -> 运行脚本 -> 关闭服务器"""
    http_proc = None
    try:
        # 1. 启动 HTTP Server
        print(f"[启动] HTTP Server (端口 {HTTP_PORT}) @ {work_dir}")
        http_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(HTTP_PORT)],
            cwd=work_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)  # 等待启动

        if http_proc.poll() is not None:
            raise Exception("HTTP Server 启动失败")

        # 2. 运行爬虫脚本
        # 入参为当前目录文件名 (即第一层文件夹名)
        print(f"[执行] 运行脚本: {os.path.basename(SPIDER_SCRIPT)}, 参数: {folder_name}")
        result = subprocess.run(
            [sys.executable, SPIDER_SCRIPT, folder_name],
            cwd=os.path.dirname(SPIDER_SCRIPT),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("[完成] 脚本执行成功。")
        else:
            print(f"[警告] 脚本执行结束 (返回码:{result.returncode})。")
            if result.stderr:
                # 打印部分错误信息以便调试
                err_msg = result.stderr.strip()
                if len(err_msg) > 200:
                    err_msg = err_msg[:200] + "..."
                print(f"       错误详情: {err_msg}")

        return True
    except Exception as e:
        print(f"[错误] 执行过程异常: {e}")
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
    print("开始批量处理 (逻辑：第一层目录即为目标)")
    print("=" * 60)

    # 确保解压根目录存在
    os.makedirs(EXTRACT_ROOT, exist_ok=True)

    zip_files = get_zip_files(SOURCE_DIR)

    if not zip_files:
        print("未找到 zip 文件。")
        return

    print(f"发现 {len(zip_files)} 个文件，开始处理...\n")

    for i, zip_file in enumerate(zip_files, 1):
        print(f"\n--- [{i}/{len(zip_files)}] {os.path.basename(zip_file)} ---")

        # 1. 解压
        if not extract_zip(zip_file, EXTRACT_ROOT):
            continue

        # 2. 定位目录 (核心修改点：获取第一层)
        target_dir = get_target_directory_v3(EXTRACT_ROOT)

        if not target_dir:
            print("[跳过] 无法定位目标目录。")
            continue

        folder_name = os.path.basename(target_dir)

        # 3. 执行任务 (启动Server -> 跑脚本 -> 停Server)
        run_process(target_dir, folder_name)

        # 4. 清理 (删除该第一层目录)
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
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断程序。")
    except Exception as e:
        print(f"\n程序发生严重错误: {e}")
        import traceback

        traceback.print_exc()