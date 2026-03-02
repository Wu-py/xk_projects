import re
import urllib
from urllib.parse import urljoin

import scrapy
from lxml import etree
from charset_normalizer import detect



class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_detail_3"

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

    def start_requests(self):
        yield scrapy.Request(
            # url="https://www.car388.com/system/second/showpic_xiang.php?lei=1&page=1&aid=24713&max=619",
            # url="https://www.car388.com/system/1994-buick-Park-avenue/showpic_xiang.php?&page=1",
            url="https://www.car388.com/system/second/showpic_xiang.php?lei=8W-01&page=15&aid=15473&max=16",
            method='GET',
            headers=self.headers,
            # cookies=self.cookies,
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

        if (div := tree.xpath('//a[contains(text(), ">>多页浏览后面页码内容")]')) and div[0].getparent() is not None:
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
        new_html.replace('文档还没结束。', '')
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
            ('*', 'src'),  # 注意：style 中的 url() 需要正则处理，较复杂
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

