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
        interface = self.get_last_route_with_ext(request.url,request.method)
        if get_interface_count(interface) < self.max_requests_per_day.get(interface, 2000):
            increment_interface_count(interface)
            return None
        else:
            logger.info(f'接口：{interface}, 请求次数已达上限，停止请求')
            spider.crawler.engine.close_spider(spider, f'接口：{interface}, 请求次数已达上限，停止请求')
            raise IgnoreRequest(str(request.body))

    def process_response(self, request, response, spider):
        if '该账号已在其它地方登录' in response.text or '会话过期' in response.text or '账号已被封禁' in response.text:
            interface = self.get_last_route_with_ext(request.url, request.method)
            print(f'接口:{interface}')
            spider.crawler.engine.close_spider(spider, '账号异常')
        return response


    def get_last_route_with_ext(self, url, method='get'):
        try:
            from urllib.parse import urlparse, unquote

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
