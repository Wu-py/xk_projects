import copy
import json
import re
import urllib
from urllib.parse import urljoin

import pymysql
import requests
import scrapy
from twisted.web.http import urlparse

from spider.changyi_pc.changyi_pc.items import ChangyiPcListItem


class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_list_3"
    table_name = "changyi_list"
    start_urls = ["https://www.car388.com/system/PC-2026/html/chex_list.php"]
    not_data_cars = []
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
            cursor.execute("SELECT * from changyi_chex where list_type = 3 and note is null and list_key not in (select distinct list_key from changyi_list) limit 5")
            rows = cursor.fetchall()
            for i in rows:
                item = ChangyiPcListItem()
                item['pp_id'] = i['pp_id']
                item['pp_name'] = i['pp_name']
                item['series'] = i['series']
                item['chex_name'] = i['chex_name']
                item['year'] = i['year']
                item['list_key'] = i['list_key']
                year_id = json.loads(i['params'])['s4']
                next_url = f'https://www.car388.com/system/chex_ziliao_s.php?s4={year_id}&c_pinpai='
                # print(next_url)
                yield scrapy.Request(
                    url=next_url,
                    method='GET',
                    headers=self.headers,
                    # cookies=self.cookies,
                    callback=self.parse_ziliao_list,
                    meta={'item': item},
                    dont_filter=True,
                )
                # break

    def parse_ziliao_list(self, response):
        item = copy.deepcopy(response.meta['item'])
        ziliao_href = response.xpath('//span[@class="ziliao_name"]/a[contains(text(), "线路图")]/@href').get()
        if not ziliao_href:
            print(item, '无线路图数据')
            self.not_data_cars.append(item['list_key'])
            return
        next_url = urljoin(response.url, ziliao_href)
        # https://www.car388.com/system/second/index.php?lei=3&s4=3953&sid=blckeoipc36191ebdol9frlcn7&saiis=8105734479639&test_id=
        # print(next_url)
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            # # cookies=self.cookies,
            callback=self.parse_get_caidan_show_url,
            meta={'item': item},
            dont_filter=True,
        )

    def parse_get_caidan_show_url(self, response):
        # print(response.text)
        item = copy.deepcopy(response.meta['item'])
        # print(item)
        # https://www.car388.com/system/second/tree.php?lei=3&che_id=&che_nianfen=3953&&pinpai_id=58&zid=&azx=&test_id=&zx=&jilid=
        src = re.search("src='(tree.php\?.+?)'", response.text).group(1)
        next_url = urljoin(response.url, src)
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            # cookies=self.cookies,
            callback=self.parse_tree,
            meta={'item': item},
            dont_filter=True,
        )

    def parse_tree(self, response):


        url = re.search('url=(.+?)>', response.text)
        if url:
            url = url.group(1)
            item = copy.deepcopy(response.meta['item'])
            # https://www.car388.com/system/second/tree_xians_ok.php?tid=24713&pinpai_id=58
            next_url = urljoin(response.url, url)
            # next_url = 'https://www.car388.com/system/second/tree_xians_ok.php?tid=24664&pinpai_id=58'
            if 'tree_xians_ok' in next_url:
                # 福特
                callback = self.parse_tree_xians_ok
            elif 'xlt.htm' in next_url:
                # 别克
                callback = self.parse_xlt
            yield scrapy.Request(
                url=next_url,
                method='GET',
                headers=self.headers,
                # cookies=self.cookies,
                callback=callback,
                meta={'item': item},
                dont_filter=True,
            )
        else:
            #         雪佛兰
            tables = response.xpath('//ul[@id="containerul"]/table[.//a]')
            for index, table in enumerate(tables, 1):
                item = copy.deepcopy(response.meta['item'])
                title = table.xpath('.//font')[0].xpath('./text()').get().strip()
                item['title_level_1'] = title
                item['index_1'] = index
                next_url = table.xpath('.//a[@href]/@href').get()
                next_url = urljoin(response.url, next_url)
                # https://www.car388.com/system/second/zi_lei_list.php?zimu_id=92&zhumu_id=3&che_nian_id=287&che_id=185
                yield scrapy.Request(
                    url=next_url,
                    method='GET',
                    headers=self.headers,
                    # cookies=self.cookies,
                    callback=self.parse_zi_lei_list,
                    meta={'item': item, 'level':2},
                    dont_filter=True,
                )

    def parse_zi_lei_list(self, response):
        tables = response.xpath('//a[text()="查看信息"]/ancestor::table[1]')
        for index, table in enumerate(tables, 1):
            item = copy.deepcopy(response.meta['item'])
            level = response.meta['level']
            a = table.xpath('.//a')[0]
            title = a.xpath('./font/text()').get().strip()
            item[f'title_level_{level}'] = title
            item[f'index_{level}'] = index
            next_url = a.xpath('./@href').get()
            next_url = urljoin(response.url, next_url)
            # https://www.car388.com/system/second/shows.php?page=1&ziliao_id=22619&zimu_id=92&zhumu_id=3&che_nian_id=287&che_id=185
            next_url = next_url.replace('shows.php', 'ziliao_message_show_fen.php')
            # https://www.car388.com/system/second/ziliao_message_show_fen.php?ziliao_id=22619&zimu_id=92&zhumu_id=3&che_nian_id=287&che_id=185&page=1
            item['filepath'] = next_url
            item['type'] = '线路图'
            # print(item)
            yield item

    def parse_xlt(self, response):
        lis = response.xpath('//ul[@id="containerul"]/li')
        for index, li in enumerate(lis, 1):
            item = copy.deepcopy(response.meta['item'])
            for i in self.get_items(li, item, 1, index):
                filepath = i['filepath'].replace('showpic', 'showpic_xiang')
                i['filepath'] = urljoin(response.url, filepath)
                i['type'] = ['线路图']
                # print(i)
                yield i

    def get_items(self, li_selector, item, level, file_index=1):
        # li_selector 是 Scrapy 的 Selector 对象

        # 1. 查找子级 ul
        ul_selectors = li_selector.xpath('./ul')

        # 2. 判断是否有子级 (SelectorList 可以直接作为布尔值判断)
        if not ul_selectors:
            # --- 叶子节点 (没有子 ul) ---
            base_item = copy.deepcopy(item)

            # 获取标题文本
            title_selector = li_selector.xpath('./a/text()')
            title = title_selector.get()  # .get() 等价于 .extract_first()

            if not title:
                return

            base_item[f'title_level_{level}'] = title.strip()
            base_item[f'index_{level}'] = file_index

            # 获取链接
            href = li_selector.xpath('./a/@href').get()
            if href:
                base_item['filepath'] = href.strip()

            yield base_item
        else:
            # --- 分支节点 (有子 ul) ---

            # 获取当前层级标题 (直接文本)
            # 注意：xpath('./text()') 可能返回多个文本节点，通常取第一个或拼接
            raw_title = li_selector.xpath('./text()').get()
            title = raw_title.strip() if raw_title else ''

            # 获取子级 li 列表
            # ul_selectors 是列表，取第一个 ul 继续查找 li
            lis = ul_selectors[0].xpath('./li')

            for index, l in enumerate(lis, 1):
                base_item = copy.deepcopy(item)
                base_item[f'title_level_{level}'] = title
                base_item[f'index_{level}'] = file_index

                # 递归调用，注意加上 self
                yield from self.get_items(l, base_item, level + 1, index)

    def parse_tree_xians_ok(self, response):
        # print(response.text)
        item = copy.deepcopy(response.meta['item'])
        url = re.search('url=(.+?)>', response.text).group(1)
        # https://www.car388.com/system/second/tree_2022.php?tid=24664&pinpai_id=58
        next_url = urljoin(response.url, url)
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            # cookies=self.cookies,
            callback=self.parse_tree_2022,
            meta={'item': item, 'level':1},
            dont_filter=True,
        )


    def parse_tree_2022(self, response):
        '''
        目录页
        '''
        # print(response.text)
        uls = response.xpath('//ul[@class="tree treeFolder collapse"]')
        item = copy.deepcopy(response.meta['item'])
        max_page = None
        for index, ul in enumerate(uls, 1):
            for i in ChangyiDianluLisSpider.parse_detail(ul, item, response.meta['level'], index):
                filepath = urljoin(response.url, i['filepath'])
                if 'tid=' in filepath:
                    yield scrapy.Request(
                        url=filepath,
                        method='GET',
                        headers=self.headers,
                        # cookies=self.cookies,
                        callback=self.parse_tree_2022,
                        meta={'item': i, 'level': response.meta['level'] + 1},
                        dont_filter=True,
                    )
                    continue
                if not max_page:
                    try:
                        cookies = response.request.cookies
                        rep = requests.get(filepath, headers=self.headers, cookies=cookies, verify=False)
                        max_page = re.search('&max=(\d+)', rep.text).group(1)
                    except Exception as e:
                        print(i, filepath, e)
                i['filepath'] = filepath.replace('showpic', 'showpic_xiang') + f'&max={max_page}'
                i['type'] = '线路图'
                yield i

    @staticmethod
    def parse_detail(ul, item, level, file_index):
        # 获取当前 ul 下的直接 li 子元素
        lis = ul.xpath('./li')
        for li in lis:
            base_item = copy.deepcopy(item)
            a_list = li.xpath('./a')
            a = a_list[0]
            href = a.xpath('./@href').get().replace(' ', '')
            title = a.xpath('string(.)').get().strip()
            base_item[f'title_level_{level}'] = title
            base_item[f'index_{level}'] = file_index
            base_item[f'filepath'] = href
            file_index += 1
            # 递归处理当前 ul 下的直接子 ul
            sub_uls = li.xpath('./ul')
            if not sub_uls:
                yield base_item
            else:
                for index, sub_ul in enumerate(sub_uls, 1):
                    yield from ChangyiDianluLisSpider.parse_detail(sub_ul, base_item, level + 1, index)

