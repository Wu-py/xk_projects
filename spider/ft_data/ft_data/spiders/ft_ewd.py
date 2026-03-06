import copy
import re
import urllib
from collections import defaultdict
from copy import deepcopy
from urllib.parse import urljoin

import pymysql
import requests
import scrapy
from lxml import etree
from spider.ft_data.ft_data.items import FtDataRepairListItem, FtDataRepairDetailItem


class FtDataSpider(scrapy.Spider):
    name = "ft_ewd"
    table_name = "ft_ewd"
    type = '电路图'
    resource_base_url = 'http://127.0.0.1:8000/manual/ewd/'
    file_id_url = defaultdict(dict)
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
            next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{date}/tree-root.xml'
            yield scrapy.Request(
                url=next_url,
                method='GET',
                headers=self.headers,
                callback=self.parse3,
                meta={'item': item}
            )
            break

    def parse3(self, response):
        '''
        一级目录页
        '''
        sections = response.xpath('//root')
        for section in sections:
            item = copy.deepcopy(response.meta['item'])
            item['title_1'] = section.xpath('./name/text()').get()
            id = section.xpath('./@id').get()
            # if id == 'intro':
            #     next_url = f'http://127.0.0.1:8000/manual/ewd/intro/intro.xml'
            #     yield scrapy.Request(
            #         url=next_url,
            #         method='GET',
            #         headers=self.headers,
            #         callback=self.parse_intro,
            #         dont_filter=True,
            #         meta={'item': item}
            #     )
            # if id == 'system':
            #     self.get_file_id_url(id)
            #     next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{item["year"]}/tree-{id}.xml'
            #     yield scrapy.Request(
            #         url=next_url,
            #         method='GET',
            #         headers=self.headers,
            #         callback=self.parse_list,
            #         dont_filter=True,
            #         meta={'item': item, 'path_id': id}
            #     )

            # if id == 'routing':
            #     self.get_file_id_url(id)
            #     next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{item["year"]}/tree-{id}.xml'
            #     yield scrapy.Request(
            #         url=next_url,
            #         method='GET',
            #         headers=self.headers,
            #         callback=self.parse_list,
            #         dont_filter=True,
            #         meta={'item': item, 'path_id': id}
            #     )

            # if id == 'fuselist':
            #     next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{item["year"]}/tree-{id}.xml'
            #     yield scrapy.Request(
            #         url=next_url,
            #         method='GET',
            #         headers=self.headers,
            #         callback=self.parse_fuselist,
            #         dont_filter=True,
            #         meta={'item': item, 'path_id': id}
            #     )

            if id == 'connlist':
                self.get_file_id_url(id)
                next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{item["year"]}/tree-{id}.xml'
                yield scrapy.Request(
                    url=next_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_list,
                    dont_filter=True,
                    meta={'item': item, 'path_id': id}
                )
                break


    def parse_list(self, response):
        '''
        二级目录页
        '''
        path_id = response.meta['path_id']
        for book in response.xpath('.//book'):
            book_name = book.xpath('./name/text()').get()
            for note in book.xpath('./note'):
                item = copy.deepcopy(response.meta['item'])
                item['title_2'] = book_name
                item['title_3'] = note.xpath('./name/text()').get()
                id = note.xpath('./@id').get()
                file_id = item['model'] + '_' + id
                item['file_id'] = file_id
                yield item

                file_name = self.file_id_url[path_id][id]
                file_url = f'http://127.0.0.1:8000/manual/ewd/contents/{path_id}/figsvg/{file_name}.svg'
                yield scrapy.Request(
                    url=file_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_detail,
                    meta={'file_id': file_id}
                )

    def parse_fuselist(self, response):
        '''
        二级目录页
        '''
        for book in response.xpath('.//book'):
            book_name = book.xpath('./name/text()').get()
            for note in book.xpath('./note'):
                item = copy.deepcopy(response.meta['item'])
                item['title_2'] = book_name
                item['title_3'] = note.xpath('./name/text()').get()
                item['file_id'] = item['model'] + '_' + 'ps-' + item['year']
                yield item

                file_url = f'http://127.0.0.1:8000/manual/ewd/contents/loads/ps-{item["year"]}.xml'
                yield scrapy.Request(
                    url=file_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_detail,
                    meta={'file_id': item['file_id']}
                )


    def parse_intro(self, response):
        '''
        二级目录页
        '''
        for Intro in response.xpath('.//Intro'):
            item = copy.deepcopy(response.meta['item'])
            item['title_2'] = Intro.xpath('./name/text()').get()
            file = Intro.xpath('./file/text()').get()
            file_id = item['model'] + '_' + file
            item['file_id'] = file_id
            file_url = f'http://127.0.0.1:8000/manual/ewd/intro/{file}.html'
            yield item
            yield scrapy.Request(
                url=file_url,
                method='GET',
                headers=self.headers,
                callback=self.parse_detail,
                meta={'file_id': file_id}
            )
            # break

    def parse_detail(self, response):
        '''
        详情页
        '''
        # return
        # print(response.text)
        item_detail = FtDataRepairDetailItem()
        item_detail['file_id'] = response.meta['file_id']
        parser = etree.HTMLParser()
        tree = etree.fromstring(response.body, parser)
        FtDataSpider.absolutize_urls(tree, self.resource_base_url)
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
            # ('script', 'xlink:href'),  # svg
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

    def get_file_id_url(self, type):
        if not self.file_id_url[type]:
            url = f'http://127.0.0.1:8000/manual/ewd/contents/{type}/title.xml'
            response = requests.get(url)
            html = etree.HTML(response.content)
            Systems = html.xpath(f'//{type}')
            for system in Systems:
                id = system.xpath('./name/@code')[0]
                file_url_name = system.xpath('./fig/text()')[0]
                self.file_id_url[type].update({id: file_url_name})

if __name__ == '__main__':
    print(urljoin('http://127.0.0.1:8000/manual/ewd/', '../../../../../system/js/ewd/fig/svgfig.js'))







