import copy
import re
import urllib
from copy import deepcopy
from urllib.parse import urljoin

import pymysql
import scrapy
from lxml import etree
from spider.ft_data.ft_data.items import FtDataRepairListItem, FtDataRepairDetailItem


class FtDataSpider(scrapy.Spider):
    name = "ft_repair"
    table_name = "ft_repair"
    headers = {
        "sec-ch-ua-platform": "\"Windows\"",
        "Referer": "http://127.0.0.1:8000/pgm/top.html",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0"
    }
    def start_requests(self):
        url = 'http://127.0.0.1:8000/pgm/js/top.js'
        yield scrapy.Request(
            url=url,
            method='GET',
            headers=self.headers,
            callback=self.parse,
        )

    def parse(self, response):
        item = FtDataRepairListItem()
        item['brand'] = '丰田'
        destination = re.search('"E": "(.+?)"', response.text).group(1)
        item['destination'] = destination
        next_url = 'http://127.0.0.1:8000/manual/pub_sys/pub-bind.xml'
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            callback=self.parse2,
            meta={'item': item}
        )

    def parse2(self, response):
        '''
        年份
        '''
        model_name = response.xpath('.//model-name/text()').get()

        term = response.xpath('.//term')
        for t in term:
            item = copy.deepcopy(response.meta['item'])
            date = t.xpath('./@date').get()
            item['model'] = model_name
            item['year'] = date
            item['type'] = '维修手册'
            # print(item)
            next_url = f'http://127.0.0.1:8000/manual/repair/control/{date}/toc-root.xml'
            yield scrapy.Request(
                url=next_url,
                method='GET',
                headers=self.headers,
                callback=self.parse3,
                meta={'item': item}
            )
            # break

    def parse3(self, response):
        '''
        一级目录页
        '''
        sections = response.xpath('//section')
        item = copy.deepcopy(response.meta['item'])
        for section in sections:
            id = section.xpath('./@id').get().strip('_')
            next_url = f'http://127.0.0.1:8000/manual/repair/control/{item["year"]}/toc-{id}.xml'
            # next_url = f'http://127.0.0.1:8000/manual/repair/control/201201/toc-004590.xml'
            yield scrapy.Request(
                url=next_url,
                method='GET',
                headers=self.headers,
                callback=self.parse4,
                # dont_filter=True,
                meta={'item': response.meta['item']}
            )
            # break

    def parse4(self, response):
        '''
        二级目录页
        '''

        for para in response.xpath('.//para'):
            item = copy.deepcopy(response.meta['item'])
            item['title_1'] = para.xpath('string(ancestor::servcat/name[1])').get()
            item['title_2'] = para.xpath('string(ancestor::section/name[1])').get()
            item['title_3'] = para.xpath('string(ancestor::ttl/name[1])').get()
            if para.xpath('./@category').get() == 'C':
                yield from self._handle_dtc_category(para, deepcopy(item))
            else:
                yield from self._handle_normal_category(para, deepcopy(item))

    def _handle_dtc_category(self, para, item):
        item['title_4'] = 'DIAGNOSTIC TROUBLE CODE CHART'
        item['title_5'] = para.xpath('./@dtccode').get()
        dtccode_id = para.xpath('./@id').get()
        item['file_id'] = dtccode_id
        # http://127.0.0.1:8000/manual/repair/contents/flow/RM1000000004C0M_flow.html
        file_url = f'http://127.0.0.1:8000/manual/repair/contents/flow/{dtccode_id}_flow.html'
        yield item
        yield scrapy.Request(
            url=file_url,
            method='GET',
            headers=self.headers,
            callback=self.parse5,
            meta={'file_id': item['file_id']}
        )

        subparas = para.xpath('./dtccode/subpara')
        for subpara in subparas:
            item2 = copy.deepcopy(item)
            item2['title_6'] = subpara.xpath('./name/text()').get()
            file_id = subpara.xpath('./@id').get().strip()
            item2['file_id'] = file_id
            file_url = f'http://127.0.0.1:8000/manual/repair/contents/{dtccode_id}.html?dummyp={file_id}'
            #         http://127.0.0.1:8000/manual/repair/contents/RM1000000004C0M.html?dummyp=RM1000000004C0M_01&PUB_TYPE=RM&MODE=2
            yield item2
            yield scrapy.Request(
                url=file_url,
                method='GET',
                headers=self.headers,
                callback=self.parse5,
                meta={'file_id': item2['file_id']}
            )

    def _handle_normal_category(self, para, item):
        item['title_4'] = para.xpath('string(name[1])').get()
        file_id = para.xpath('./@id').get().strip()
        item['file_id'] = file_id
        file_url = f'http://127.0.0.1:8000/manual/repair/contents/{file_id}.html'
        yield item
        yield scrapy.Request(
            url=file_url,
            method='GET',
            headers=self.headers,
            callback=self.parse5,
            meta={'file_id': item['file_id']}
        )

    def parse5(self, response):
        '''
        详情页
        '''
        # return
        # print(response.text)
        item_detail = FtDataRepairDetailItem()
        item_detail['file_id'] = response.meta['file_id']
        parser = etree.HTMLParser()
        tree = etree.fromstring(response.body, parser)

        for a in tree.xpath('//a'):
            a.getparent().remove(a)

        FtDataSpider.absolutize_urls(tree, response.url)
        new_html = etree.tostring(tree, encoding='unicode', method='html')
        item_detail['content'] = new_html
        yield item_detail


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
            ('link', 'href'),  # 注意：style 中的 url() 需要正则处理，较复杂
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







