# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
from urllib.parse import urlparse, unquote

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import IgnoreRequest
from scrapy.middleware import logger

from interface_count import get_interface_count, increment_interface_count, init_file


class ChangyiPcDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    def __init__(self):
        init_file()
        self.max_requests_per_day = {
        }

    def process_request(self, request, spider):
        interface = self.get_last_route_with_ext(request.url)
        if get_interface_count(interface) < self.max_requests_per_day.get(interface, 1000):
            increment_interface_count(interface)
            return None
        else:
            logger.info(f'接口：{interface}, 请求次数已达上限，停止请求')
            spider.crawler.engine.close_spider(spider, f'接口：{interface}, 请求次数已达上限，停止请求')
            raise IgnoreRequest(str(request.body))

    def process_response(self, request, response, spider):
        if '该账号已在其它地方登录' in response.text or '会话过期' in response.text or '账号已被封禁' in response.text:
            interface = self.get_last_route_with_ext(request.url)
            print(f'接口:{interface}')
            spider.crawler.engine.close_spider(spider, '账号异常')
        return response

    def get_last_route_with_ext(self, url):
        """
        获取URL的最后一个路由名称（含文件扩展名）

        示例:
            https://www.car388.com/system/second/tree_2022.php?tid=24664&pinpai_id=58
            返回: tree_2022.php

        :param url: 完整的URL字符串
        :return: 最后一个路由名称 + 扩展名 (str)，如果无法提取则返回 None
        """
        try:
            # 1. 解析URL，获取path部分（自动去除查询参数?xxx和锚点#xxx）
            parsed = urlparse(url)
            path = unquote(parsed.path)  # 解码URL编码字符，如 %20 → 空格

            # 2. 清理末尾斜杠，避免 basename 返回空
            path = path.rstrip('/')

            # 3. 提取最后一个路径部分
            last_part = os.path.basename(path)

            # 4. 返回结果（空则返回None）
            return last_part if last_part else None

        except Exception as e:
            print(f"解析URL出错: {e}")
            return None

