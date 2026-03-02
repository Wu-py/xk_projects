import re
import urllib
from urllib.parse import urljoin

import pymysql
import scrapy
from lxml import etree

from spider.changyi_pc.changyi_pc.items import ChangyiDetailItem


class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_detail_2"
    table_name = "changyi_detail"
    handle_httpstatus_list = [403]
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
    # cookies = {
    #             "_UUID_UV": "1769479948471149",
    #             "53gid2": "17258468377003",
    #             "53revisit": "1769479966488",
    #             "__utmz": "139703073.1769500252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
    #             "__utma": "139703073.1164173733.1769500252.1769502953.1770374162.3",
    #             "Hm_lvt_decbe98a86b71fe465bb5c6a3983c4e8": "1769501690,1772084854",
    #             "PHPSESSID": "vmmmi4mn9lkebcip8r5bhrhop3"
    #         }

    def start_requests(self):
        self.connection = pymysql.connect(
            host=self.settings.get('MYSQL_HOST'),
            user=self.settings.get('MYSQL_USER'),
            password=self.settings.get('MYSQL_PASSWORD'),
            database=self.settings.get('MYSQL_DB'),
            port=self.settings.get('MYSQL_PORT'),
            charset='utf8mb4',  # 设置编码
            cursorclass=pymysql.cursors.DictCursor  # 返回字典格式的行
        )
        self.cursor = self.connection.cursor()

        with self.connection.cursor() as cursor:
            sql = '''
            SELECT DISTINCT t1.filepath
            FROM changyi_list t1
            INNER JOIN changyi_chex t2 ON t1.list_key = t2.list_key
            LEFT JOIN changyi_detail td ON t1.filepath = td.filepath
            WHERE t2.list_type = 2
              AND td.filepath IS NULL limit 50; 
            '''
            cursor.execute(sql)
            rows = cursor.fetchall()
            for i in rows:
                item = ChangyiDetailItem()
                item['filepath'] = i['filepath']
                yield scrapy.Request(
                    # url="https://qx.car388.com/CarHtml/Volvo/diag/39250552/index.html?",
                    # url="https://qx.car388.com/CarHtml/ISTA/html/2000011314556.html",
                    url=item['filepath'],
                    method='GET',
                    headers=self.headers,
                    # cookies=self.cookies,
                    callback=self.parse,
                    meta={'item': item}
                )

    def parse(self, response):
        # 将 response 转为可修改的 lxml 文档
        # print(response.text)
        item = response.meta['item']
        if response.status == 200:
            parser = etree.HTMLParser()
            tree = etree.fromstring(response.text, parser)

            for script in tree.xpath('//script'):
                script.getparent().remove(script)
            for font in tree.xpath('(//body/font[following-sibling::meta])[position() <= 2]'):
                font.getparent().remove(font)

            if (div := tree.xpath('//div[@id="tool-container"]')) and div[0].getparent() is not None:
                div[0].getparent().remove(div[0])

            ChangyiDianluLisSpider.absolutize_urls(tree, response.url)

            # 获取修改后的 HTML 字符串
            new_html = etree.tostring(tree, encoding='unicode', method='html')
            item['html'] = new_html
            yield item
        else:
            item['html'] = response.status
            yield item

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

