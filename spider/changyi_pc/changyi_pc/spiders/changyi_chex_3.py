import copy
import json
import re
import urllib
from urllib.parse import urljoin

import pymysql
import requests
import scrapy
from twisted.web.http import urlparse

from spider.changyi_pc.changyi_pc.items import ChangyiPcListItem, ChangyiChexItem


class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_chex_3"
    table_name = "changyi_chex"
    start_urls = ["https://www.car388.com/system/PC-2026/html/chex_list.php"]

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
            cursor.execute("SELECT * from pp_table where list_type_2 != 1 and pp_id not in (select distinct pp_id from changyi_chex) limit 1")
            # cursor.execute("SELECT * from pp_table where pp_name = 'MINI'")
            rows = cursor.fetchall()
            for i in rows:
                pp_id = i['pp_id']
                pp_name = i['pp_name']
                # pp_id = '62'
                # pp_name = 'Chrysler(克莱斯勒)'
                item = ChangyiChexItem()
                item['pp_id'] = pp_id
                item['pp_name'] = pp_name
                yield scrapy.Request(
                    url=self.start_urls[0] + f'?pinpai_id={pp_id}',
                    method='GET',
                    headers=self.headers,
                    # cookies=self.cookies,
                    callback=self.parse_chex_list,
                    meta={'item':item},
                )

    def parse_chex_list(self, response):
        # print(response.text)
        li_list = response.xpath("//li[@class='main7li']")
        for li in li_list:
            item = copy.deepcopy(response.meta['item'])
            chex_name = li.xpath('.//center/text()').extract_first()
            chex_href = li.xpath('./a/@href').extract_first()
            # print(chex_href)
            chex_id = re.search('chex_id=(\d+)', chex_href).group(1)
            # test
            # if chex_id != '3691':
            #     continue
            # print(chex_name, chex_id)

            item['chex_name'] = chex_name
            # https://www.car388.com/system/chex_ziliao_che.php?pinpai_id=242&chex_id=3706&pinpai_name&chex_name=阿维塔06
            yield scrapy.Request(
                url=chex_href,
                method='GET',
                headers=self.headers,
                # cookies=self.cookies,
                callback=self.parse_year_list,
                meta={'item': item},
            )
            # break

    def parse_year_list(self, response):
        # print(response.text)
        tr_list = response.xpath("//tr[.//a]")
        for tr in tr_list:
            item = copy.deepcopy(response.meta['item'])
            year = tr.xpath('.//div[@class="STYLE6"]/font/text()').extract_first()
            year = re.search(r'(\d+[-\d]*)', year).group(1)
            year_href = tr.xpath('.//a/@href').extract_first()
            year_id = re.search('s4=(\d+)', year_href).group(1)
            item['year'] = year
            item['list_type'] = 3
            # next_url = f'https://www.car388.com/system/chex_ziliao_s.php?s4={year_id}&c_pinpai='
            item['params'] = json.dumps({'s4': year_id}, ensure_ascii=False)
            # print(item)
            yield item