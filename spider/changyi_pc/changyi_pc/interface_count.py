import json
import datetime
import os
import threading

# 配置文件路径
FILE_PATH = 'interface_request_count.json'
# 创建线程锁，防止多线程同时写入导致数据冲突
file_lock = threading.Lock()


def init_file():
    """初始化文件，如果不存在则创建空 JSON 文件"""
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'w', encoding='utf-8') as file:
            json.dump({}, file, ensure_ascii=False, indent=4)


def _load_data():
    """内部辅助函数：读取数据"""
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_data(data):
    """内部辅助函数：保存数据"""
    with open(FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_interface_count(interface, date=None):
    """
    获取指定日期、指定接口的请求次数
    :param interface: 接口名称 (如 '/api/login')
    :param date: 日期字符串 (如 '2023-10-27'), 默认为今天
    :return: 请求次数 (int)
    """
    if date is None:
        date = datetime.date.today().isoformat()

    with file_lock:
        data = _load_data()

    # 按照目标格式：{'日期': {'接口': 次数}}
    if date in data and interface in data[date]:
        return data[date][interface]
    return 0


def increment_interface_count(interface, date=None):
    """
    增加指定日期、指定接口的请求次数
    :param interface: 接口名称
    :param date: 日期字符串，默认为今天
    """
    if date is None:
        date = datetime.date.today().isoformat()

    with file_lock:
        data = _load_data()

        # 如果该日期不存在，初始化该日期的字典
        if date not in data:
            data[date] = {}

        # 如果该接口在该日期下不存在，初始化为 0
        if interface not in data[date]:
            data[date][interface] = 0

        # 计数 +1
        data[date][interface] += 1

        _save_data(data)


if __name__ == '__main__':
    # 1. 初始化文件
    init_file()

    # 2. 示例配置
    interfaces = ['login']
    max_requests_per_day = 15

    print(f"开始模拟请求，日期：{datetime.date.today().isoformat()}")

    # 3. 模拟不同接口的请求
    # 为了演示，我们循环模拟不同接口的请求
    for i in range(10):
        # 轮流请求不同的接口
        current_interface = interfaces[i % len(interfaces)]

        # 获取当前接口今天的已请求次数
        count = get_interface_count(current_interface)

        if count < max_requests_per_day:
            # 执行请求逻辑
            # requests.get(url...)
            increment_interface_count(current_interface)
            print(f"[{i + 1}] 接口：{current_interface}, 当前次数：{count + 1}")
        else:
            print(f"[{i + 1}] 接口：{current_interface} 请求次数已达上限 ({max_requests_per_day})")

    # 4. 验证结果
    print("\n--- 最终统计 ---")
    for iface in interfaces:
        c = get_interface_count(iface)
        print(f"接口 {iface}: {c} 次")