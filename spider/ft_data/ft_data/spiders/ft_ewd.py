import base64
import copy
import datetime
import hashlib
import re
import urllib
from collections import defaultdict
from copy import deepcopy
from urllib.parse import urljoin

import pymysql
import requests
import scrapy
from charset_normalizer import from_bytes
from lxml import etree
from spider.ft_data.ft_data.items import FtDataRepairListItem, FtDataRepairDetailItem
from spider.ft_data.ft_data.tools import get_filename_from_url, upload_file_to_oss, upload_file_to_oss_async


class FtDataSpider(scrapy.Spider):
    name = "ft_ewd"
    table_name = "ft_ewd"
    type = '电路图'
    resource_base_url = 'http://127.0.0.1:8000/manual/ewd/'
    file_id_url = defaultdict(dict)
    file_name_md5_list = []
    oss_prefix = 'cl_ft'
    oss_baseurl = 'https://xingka-car-data.oss-cn-shenzhen.aliyuncs.com'
    headers = {
        "sec-ch-ua-platform": "\"Windows\"",
        "Referer": "http://127.0.0.1:8000/pgm/top.html",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0"
    }
    
    def __init__(self, *args, **kwargs):
        super(FtDataSpider, self).__init__(*args, **kwargs)


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
            # break

    def parse3(self, response):
        '''
        一级目录页
        '''
        sections = response.xpath('//root')
        for section in sections:
            item = copy.deepcopy(response.meta['item'])
            item['title_1'] = section.xpath('./name/text()').get()
            id = section.xpath('./@id').get()
            if id == 'intro':
                next_url = f'http://127.0.0.1:8000/manual/ewd/intro/intro.xml'
                yield scrapy.Request(
                    url=next_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_intro,
                    dont_filter=True,
                    meta={'item': item}
                )
            if id == 'system':
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

            if id == 'routing':
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

            if id == 'fuselist':
                next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{item["year"]}/tree-{id}.xml'
                yield scrapy.Request(
                    url=next_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_fuselist,
                    dont_filter=True,
                    meta={'item': item, 'path_id': id}
                )

            if id == 'connlist':
                self.get_connlist_file_id_url(id)
                next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{item["year"]}/tree-{id}.xml'
                yield scrapy.Request(
                    url=next_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_connlist,
                    dont_filter=True,
                    meta={'item': item, 'path_id': id}
                )

            if id == 'overall':
                self.get_file_id_url(id)
                next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{item["year"]}/tree-{id}.xml'
                yield scrapy.Request(
                    url=next_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_overall,
                    dont_filter=True,
                    meta={'item': item, 'path_id': id}
                )



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
                file_name = self.file_id_url[path_id][id]
                file_id = self.directory + '_' + file_name
                item['file_id'] = file_id
                yield item
                file_url = f'http://127.0.0.1:8000/manual/ewd/contents/{path_id}/figsvg/{file_name}.svg'
                oss_url = self.get_oss_url(file_url)
                item_detail = FtDataRepairDetailItem()
                item_detail['file_id'] = file_id
                item_detail['content'] = oss_url
                item_detail['content_type'] = 'svg'
                yield item_detail


    def parse_overall(self, response):
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
                file_name = self.file_id_url[path_id][id]
                file_id = self.directory + '_' + file_name
                item['file_id'] = file_id
                yield item

                file_url = f'http://127.0.0.1:8000/manual/ewd/contents/{path_id}/pdf/{file_name}.pdf'
                oss_url = self.get_oss_url(file_url)
                item_detail = FtDataRepairDetailItem()
                item_detail['file_id'] = file_id
                item_detail['content'] = oss_url
                item_detail['content_type'] = 'pdf'
                yield item_detail

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
                item['file_id'] = self.directory + '_' + 'ps-' + item['year']
                yield item

                file_url = f'http://127.0.0.1:8000/manual/ewd/contents/loads/ps-{item["year"]}.xml'
                yield scrapy.Request(
                    url=file_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_detail,
                    meta={'file_id': item['file_id']}
                )

    def parse_connlist(self, response):
        '''
        二级目录页
        '''
        for book in response.xpath('./book'):
            book_name = book.xpath('./name/text()').get()
            for book2 in book.xpath('./book'):
                item = copy.deepcopy(response.meta['item'])
                item['title_2'] = book_name
                item['title_3'] = book2.xpath('./name/text()').get()
                id = book2.xpath('./@id').get()
                next_url = f'http://127.0.0.1:8000/manual/ewd/contents/tree/{item["year"]}/tree-{id}.xml'
                yield scrapy.Request(
                    url=next_url,
                    method='GET',
                    headers=self.headers,
                    callback=self.parse_connlist_2,
                    dont_filter=True,
                    meta={'item': item}
                )

    def parse_connlist_2(self, response):
        '''
        二级目录页
        '''
        for note in response.xpath('//note'):
            item = copy.deepcopy(response.meta['item'])
            title_4 = note.xpath('./name/text()').get()
            code = note.xpath('./@code').get()
            item['title_4'] = title_4 + ' / ' + code
            file_url_name = self.file_id_url['connlist'][code]
            file_id = self.directory + '_' + code
            item['file_id'] = file_id
            yield item

            file_url = f'http://127.0.0.1:8000/manual/ewd/contents/connector/figsvg/{file_url_name}.svg'
            oss_url = self.get_oss_url(file_url)
            item_detail = FtDataRepairDetailItem()
            item_detail['file_id'] = file_id
            item_detail['content'] = oss_url
            item_detail['content_type'] = 'svg'
            yield item_detail

    def parse_intro(self, response):
        '''
        二级目录页
        '''
        for Intro in response.xpath('.//Intro'):
            item = copy.deepcopy(response.meta['item'])
            item['title_2'] = Intro.xpath('./name/text()').get()
            file = Intro.xpath('./file/text()').get()
            file_id = self.directory + '_' + file
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
        self.absolutize_urls(tree, self.resource_base_url)
        new_html = etree.tostring(tree, encoding='unicode', method='html')
        item_detail['content'] = new_html
        item_detail['content_type'] = 'html'
        yield item_detail


    def absolutize_urls(self, tree, base_url):
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
                    oss_url = self.get_oss_url(absolute_url)
                    if oss_url:
                        elem.set(attr, oss_url)


    def get_oss_url(self, url):
        absolute_url = url

        file_name, suffix = get_filename_from_url(absolute_url)
        if suffix in ['.js', '.css']:
            file_name_md5 = hashlib.md5(('ft' + file_name).encode('utf-8')).hexdigest() + suffix
        else:
            file_name_md5 = hashlib.md5(('ft' + self.directory + file_name).encode('utf-8')).hexdigest() + suffix
        if file_name_md5 not in self.file_name_md5_list:
            file_response = requests.get(absolute_url)
            response_text = base64.b64encode(file_response.content).decode()
            upload_file_to_oss_async(response_text, file_name_md5, prefix=self.oss_prefix)
            oss_url = self.oss_baseurl + '/' + self.oss_prefix + '/' + datetime.date.today().strftime('%Y-%m-%d') + '/' + file_name_md5
            self.file_name_md5_list.append(file_name_md5)
        else:
            oss_url = self.oss_baseurl + '/' + self.oss_prefix + '/' + datetime.date.today().strftime('%Y-%m-%d') + '/' + file_name_md5
        return oss_url


    def get_file_id_url(self, type):
        if not self.file_id_url[type]:
            url = f'http://127.0.0.1:8000/manual/ewd/contents/{type}/title.xml'
            response = requests.get(url)
            html = etree.HTML(response.content)
            if type == 'overall':
                Systems = html.xpath(f'//system')
            else:
                Systems = html.xpath(f'//{type}')
            for system in Systems:
                id = system.xpath('./name/@code')[0]
                file_url_name = system.xpath('./fig/text()')[0]
                self.file_id_url[type].update({id: file_url_name})

    def get_connlist_file_id_url(self, type):
        if not self.file_id_url[type]:
            url = f'http://127.0.0.1:8000/manual/ewd/contents/connector/parts.xml'
            response = requests.get(url)
            html = etree.HTML(response.content)
            CodedItems = html.xpath('//codeditem[fig[normalize-space()]]')

            for CodedItem in CodedItems:
                code = CodedItem.xpath('./@code')[0]
                subcode = CodedItem.xpath('./@subcode')
                if subcode:
                    code = code + '-' + subcode[0]
                file_url_name = CodedItem.xpath('./fig/text()')[0]
                self.file_id_url[type].update({code: file_url_name})

if __name__ == '__main__':
    print(urljoin('http://127.0.0.1:8000/manual/ewd/', '../../../../../system/js/ewd/fig/svgfig.js'))







