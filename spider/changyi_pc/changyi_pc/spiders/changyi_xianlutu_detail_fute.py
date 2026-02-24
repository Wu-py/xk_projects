import re
import urllib
from urllib.parse import urljoin

import scrapy
from lxml import etree
from charset_normalizer import detect



class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_xianlutu_detail_fute"

    headers = {
        "Host": "www.car388.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) app/2025.8.7 Chrome/108.0.5359.215 CoreVer/22.3.3 Safari/537.36 LT-PC/Win/2201/166",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "iframe",
        "Referer": "https://www.car388.com/system/chex_ziliao_che.php?pinpai_id=58&chex_id=2092&pinpai_name&chex_name=Bronco%20Sport",
        "Accept-Language": "zh-CN"
    }
    cookies = {
        "_UUID_UV": "1769479948471149",
        "53gid2": "17258468377003",
        "53revisit": "1769479966488",
        "__utmz": "139703073.1769500252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
        "Hm_lvt_decbe98a86b71fe465bb5c6a3983c4e8": "1769501690",
        "__utma": "139703073.1164173733.1769500252.1769502953.1770374162.3",
        "PHPSESSID": "mq6eq7m0s20rd1s08lo51n1qe5",
        "53kf_72099103_from_host": "www.car388.com",
        "53kf_72099103_keyword": "https%3A%2F%2Fwww.car388.com%2Fsystem%2F2019-2%2Findex.php",
        "uuid_53kf_72099103": "19249d0e5fbd54fe5c5c4eef29ddc8df",
        "53kf_72099103_land_page": "https%253A%252F%252Fwww.car388.com%252Fsystem%252FPC-2026%252Findex.php",
        "kf_72099103_land_page_ok": "1"
    }

    def start_requests(self):
        yield scrapy.Request(
            url="https://www.car388.com/system/second/showpic_xiang.php?lei=1&page=1&aid=24713&max=619",
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse,
        )

    def parse(self, response):
        # 将 response 转为可修改的 lxml 文档

        result = detect(response.body)
        encoding = result['encoding']
        parser = etree.HTMLParser(encoding=encoding)
        tree = etree.fromstring(response.body, parser)

        for script in tree.xpath('//script'):
            script.getparent().remove(script)

        if (div := tree.xpath('//div[@id="page_ge"]')) and div[0].getparent() is not None:
            div[0].getparent().remove(div[0])
        if (div := tree.xpath('//div[@id="yulan"]')) and div[0].getparent() is not None:
            div[0].getparent().remove(div[0])
        if (div := tree.xpath('//div[@id="tu"]')) and div[0].getparent() is not None:
            div[0].getparent().remove(div[0])
        if (div := tree.xpath('//span[contains(text(), "文档还没结束。")]')) and div[0].getparent() is not None:
            div[0].getparent().remove(div[0])
        targets = tree.xpath('//font[contains(text(), "矢量浏览该图")]')
        for node in targets:
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)
        targets = tree.xpath('//*[contains(text(), "畅易")]')
        for node in targets:
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)

        ChangyiDianluLisSpider.absolutize_urls(tree, response.url)

        # 获取修改后的 HTML 字符串
        new_html = etree.tostring(tree, encoding='unicode', method='html')
        print(new_html)

    @staticmethod
    def absolutize_urls(tree, base_url):
        """
        将 HTML 文档中所有相对 URL 补全为绝对 URL。

        支持的元素和属性：
          - <a>, <link> 的 href
          - <img>, <script>, <iframe>, <video>, <audio>, <source>, <track> 的 src
          - 可选：自定义 data-* 属性（如 data-src, data-url）——本例暂不启用，可按需添加
        """
        # 定义需要处理的 (标签名, 属性名) 列表
        url_attributes = [
            # ('a', 'href'),
            # ('link', 'href'),
            # ('img', 'src'),
            # ('script', 'src'),
            # ('iframe', 'src'),
            # ('video', 'src'),
            # ('audio', 'src'),
            # ('source', 'src'),
            # ('track', 'src'),
            # 如需处理背景图等，可加：
            # ('*', 'href'),  # 注意：style 中的 url() 需要正则处理，较复杂
            ('*', 'src'),  # 注意：style 中的 url() 需要正则处理，较复杂
            ('div', 'data-page-url'),  # 注意：style 中的 url() 需要正则处理，较复杂
        ]

        for tag, attr in url_attributes:
            # 使用 XPath 选择所有具有该属性的指定标签
            xpath_expr = f'//{tag}[@{attr}]'
            for elem in tree.xpath(xpath_expr):
                current_value = elem.get(attr)
                if current_value and not current_value.startswith(
                        ('http://', 'https://', 'mailto:', 'tel:', '#', 'javascript:')):
                    # 补全为绝对 URL
                    absolute_url = urljoin(base_url, current_value)
                    elem.set(attr, absolute_url)

        # 可选：处理任意标签上的 data-src 或 data-url（取消注释即可启用）
        # for attr_name in ['data-src', 'data-url']:
        #     for elem in tree.xpath(f'//*[@{attr_name}]'):
        #         val = elem.get(attr_name)
        #         if val and not val.startswith(('http://', 'https://', 'mailto:', 'tel:', '#', 'javascript:')):
        #             elem.set(attr_name, urljoin(base_url, val))


