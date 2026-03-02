# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
import re
import threading
from urllib.parse import urlparse, unquote

import requests
from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import IgnoreRequest
from scrapy.middleware import logger
from urllib.parse import urlparse, unquote

from interface_count import get_interface_count, increment_interface_count, init_file
from spider.changyi_pc.changyi_pc.account_manager import AccountManager


def _login(cookies, MachineId, loginid, loginpwd):
    if cookies.get('PHPSESSID', None):
        del cookies['PHPSESSID']
    headers = {
        "Host": "www.car388.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) app/2025.8.7 Chrome/108.0.5359.215 CoreVer/22.3.3 Safari/537.36 LT-PC/Win/2201/166",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "zh-CN"
    }

    url = "https://www.car388.com/system/t_cs_2025.php"
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    PHPSESSID = re.search(r'PHPSESSID=(.+?);', response.headers['Set-Cookie']).group(1)

    cookies['PHPSESSID'] = PHPSESSID
    url = "https://www.car388.com/system/t_cs_2025.php"
    params = {
        "MachineId": MachineId
    }
    requests.get(url, headers=headers, cookies=cookies, params=params, verify=False)


    url = "https://www.car388.com/system/t_cs_2025.php"
    requests.get(url, headers=headers, cookies=cookies, verify=False)

    url = "https://www.car388.com/system/index_new_2025.php"
    params = {
        "StrCPUSN": "",
        "PSchoolID": "CY20MX01200",
        "PNetworkID": f"2222-{MachineId}",
        "StrVer": "",
        "y": "",
        "ms": "",
        "PNetworkID2": ""
    }
    requests.get(url, headers=headers, cookies=cookies, params=params, verify=False)

    url = "https://www.car388.com/system/denglu_ok_2_2025.php"
    params = {
        "loginid": loginid,
        "loginpwd": loginpwd,
        "action": "check",
        "PNetworkID": f"2222-{MachineId}",
        "StrCPUSN": "",
        "PSchoolID": "CY20MX01200",
        "StrVer": ""
    }
    requests.get(url, headers=headers, cookies=cookies, params=params, verify=False)

    url = "https://www.car388.com/system/index_new_2025.php"
    params = {
        "PNetworkID": f"2222-{MachineId}",
        "PSchoolID": "CY20MX01200",
        "StrVer": "",
        "StrCPUSN": "",
        "sid": PHPSESSID,
        "dl": "1",
        "dl_id": ""
    }
    requests.get(url, headers=headers, cookies=cookies, params=params, verify=False)
    return cookies

def login(account_name, manager):
    account_info = manager.get_account(account_name)
    cookies = account_info['cookies']
    MachineId = account_info['MachineId']
    loginid = account_info['loginid']
    loginpwd = account_info['loginpwd']
    new_cookies = _login(cookies, MachineId, loginid, loginpwd)
    return new_cookies


class AccountCookieMiddleware:
    """
    Scrapy 下载中间件：
    在每次请求前，轮训获取一个账号的 cookies 并添加到 request 中
    """

    def __init__(self, json_file, index_file):
        # 初始化账号管理器
        self.manager = AccountManager(json_file=json_file, index_file=index_file)
        # 线程锁：防止多线程/并发下 current_index 和文件写入冲突
        # Scrapy 虽然主要是异步，但在某些配置或扩展下可能涉及多线程，且 AccountManager 非线程安全
        self.lock = threading.Lock()

    @classmethod
    def from_crawler(cls, crawler):
        """
        Scrapy 标准初始化方法，从 settings 获取配置
        """
        # 从 settings.py 读取配置，如果没有则使用默认值
        json_file = crawler.settings.get('ACCOUNT_JSON_FILE', 'accounts.json')
        index_file = crawler.settings.get('ACCOUNT_INDEX_FILE', 'account_index.json')

        middleware = cls(json_file, index_file)

        # 绑定信号，可以在爬虫关闭时做一些清理工作（可选）
        # crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        """
        每个请求发出前都会调用此方法
        """
        # 加锁确保获取账号和更新索引的原子性
        with self.lock:
            account_name, account_info = self.manager.get_next_account(save_index=True)
        if account_name and account_info:
            # 从账号信息中提取 cookies
            # 注意：确保 accounts.json 中的账号信息字典里包含 'cookies' 键
            cookies = account_info.get('cookies', {})

            if cookies:
                # 将 cookies 赋值给 request
                request.cookies = cookies

                # (可选) 将账号名存入 meta，方便在 Spider 或 Pipeline 中知道当前请求用的是哪个账号
                request.meta['account_name'] = account_name
                logger.debug(f"Request {request.url} using account: {account_name}")
            else:
                logger.warning(f"Account {account_name} found but no cookies available.")
        else:
            logger.warning("No available accounts found in AccountManager.")

        # 返回 None 表示继续处理请求
        return None

    def process_response(self, request, response, spider):
        if '请登录后使用' in response.text or ('list' in spider.name and './denglu_fail.php' in response.text):
            account_name = request.meta['account_name']
            new_cookies = login(account_name, self.manager)
            self.manager.update_cookies(account_name, new_cookies)
            request.dont_filter = True
            return request
        return response


class ChangyiPcDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    def __init__(self):
        init_file()
        self.max_requests_per_day = {
        }

    def process_request(self, request, spider):
        interface = self.get_last_route_with_ext(request.url,request.method)
        if get_interface_count(interface) < self.max_requests_per_day.get(interface, 2000):
            increment_interface_count(interface)
            return None
        else:
            logger.info(f'接口：{interface}, 请求次数已达上限，停止请求')
            spider.crawler.engine.close_spider(spider, f'接口：{interface}, 请求次数已达上限，停止请求')
            raise IgnoreRequest(str(request.body))


    def process_response(self, request, response, spider):
        if '您访问频率过高' in response.text:
            accout_name = request.meta['account_name']
            spider.crawler.engine.close_spider(spider, f'账号访问频率过高：{accout_name}')
        return response



    def get_last_route_with_ext(self, url, method='get'):
        try:

            # 1. 解析URL，获取path和query部分
            parsed = urlparse(url)
            path = unquote(parsed.path)  # 解码URL编码字符，如 %20 → 空格

            # 2. 清理末尾斜杠，避免分割出空字符串
            path = path.rstrip('/')

            # 3. 分割路径并过滤空部分，得到纯净的路径列表
            path_parts = [p for p in path.split('/') if p]

            # 4. 边界处理：路径为空时直接返回None
            if not path_parts:
                return None

            # 5. 判断是否满足特殊条件：GET请求 且 无查询参数
            is_get_no_params = method.lower() == 'get' and not parsed.query.strip()

            if is_get_no_params and len(path_parts) >= 2:
                # ✅ 满足条件：返回倒数第二个路径部分（如 'second'）
                return path_parts[-2]
            else:
                # ✅ 默认逻辑：返回最后一个路径部分（含扩展名，如 'tree_2022.html'）
                return path_parts[-1]

        except Exception as e:
            print(f"解析URL出错: {e}")
            return None

if __name__ == '__main__':
    # account_name = '19876775931'
    # manager = AccountManager('accounts.json')
    # new_cookies = login(account_name, manager)
    # manager.update_cookies(account_name, new_cookies)

    manager = AccountManager('accounts.json')
    for i in range(10):
        a = manager.get_next_account(save_index=True)
        print(a)
