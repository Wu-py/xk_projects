import re
import urllib
from urllib.parse import urljoin

import scrapy
from lxml import etree



class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_dianlutu_detail_2"

    headers = {
        'Host': 'qx.car388.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) çææ±½ä¿®å¹³å°V9/2025.8.7 Chrome/108.0.5359.215 Electron/22.3.3 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Dest': 'iframe',
        'Referer': 'https://qx.car388.com/plugin.php?id=qssy_api&ac=carview&url=Q2FySHRtbC9JU1RBL2h0bWwvMjAwMDAxMTMxNDU1Ni5odG1s&tipps=&Height=760&table_link=21729&table_name=10&language=zh-Hans&type=app&title=[FUB]%20LIN%20%E6%80%BB%E7%BA%BF%E4%B8%8A%E7%9A%84%E8%AF%8A%E6%96%ADV.12',
        'Accept-Language': 'zh-CN',
    }
    cookies = {
        "53gid2": "17258468377003",
        "53gid1": "17258468377003",
        "visitor_type": "old",
        "53gid0": "17258468377003",
        "53uvid": "1",
        "onliner_zdfq72099103": "0",
        "_UUID_UV": "1769479948471149",
        "53revisit": "1769479966488",
        "__utmz": "139703073.1769500252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
        "Hm_lvt_decbe98a86b71fe465bb5c6a3983c4e8": "1769501690",
        "__utma": "139703073.1164173733.1769500252.1769502953.1770374162.3",
        "PHPSESSID": "fsf7c0ipvr3enmhdbbknof6al4",
        "53kf_72099103_from_host": "www.car388.com",
        "uuid_53kf_72099103": "d1d198ac44624ee423fabdfb4ea9fe63",
        "53kf_72099103_land_page": "https%253A%252F%252Fwww.car388.com%252Fsystem%252FPC-2026%252Findex.php",
        "kf_72099103_land_page_ok": "1",
        "53kf_72099103_keyword": "https%3A%2F%2Fqx.car388.com%2F"
    }

    def start_requests(self):
        yield scrapy.Request(
            url="https://qx.car388.com/CarHtml/Volvo/diag/39250552/index.html?",
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse,
        )

    def parse(self, response):
        # 将 response 转为可修改的 lxml 文档
        # print(response.text)
        parser = etree.HTMLParser()
        tree = etree.fromstring(response.text, parser)

        for script in tree.xpath('//script'):
            script.getparent().remove(script)

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
            ('*', 'href'),  # 注意：style 中的 url() 需要正则处理，较复杂
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


