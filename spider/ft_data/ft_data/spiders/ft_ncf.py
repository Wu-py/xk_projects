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
    name = "ft_ncf"
    table_name = "ft_ncf"
    type = '新车特征'
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
            item['type'] = self.type
            # print(item)
            next_url = f'http://127.0.0.1:8000/manual/ncf/control/{date}/toc-root.xml'
            yield scrapy.Request(
                url=next_url,
                method='GET',
                headers=self.headers,
                callback=self.parse3,
                meta={'item': item}
            )

    def parse3(self, response):
        '''
        一级目录页
        '''
        sections = response.xpath('//section')
        item = copy.deepcopy(response.meta['item'])
        for section in sections:
            id = section.xpath('./@id').get().strip('_')
            next_url = f'http://127.0.0.1:8000/manual/ncf/control/{item["year"]}/toc-{id}.xml'
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
            if para.xpath('./@category').get() == 'F':
                yield from self._handle_f_category(para, deepcopy(item))
            else:
                raise ValueError('ttttttttttttttttt', item)

    def _handle_f_category(self, para, item):
        item['title_5'] = para.xpath('string(name[1])').get()
        file_id = para.xpath('./@id').get().strip()
        item['file_id'] = file_id
        file_url = f'http://127.0.0.1:8000/manual/ncf/contents/{file_id}.html'
        item['title_4'] = para.xpath('./ncf-para/name/text()').get()
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







