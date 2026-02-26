import copy
import json
import re
import urllib
from operator import index
from urllib.parse import urlencode, urlparse, unquote

import pymysql
import scrapy

from spider.changyi_pc.changyi_pc.items import ChangyiPcListItem, ChangyiChexItem


class ChangyiDianluLisSpider(scrapy.Spider):
    '''
    劳斯莱斯
    '''
    name = "changyi_chex_2"
    table_name = "changyi_chex"
    start_urls = ["https://qx.car388.com/plugin.php?id=qssy_api:car"]

    headers = {
        "Host": "qx.car388.com",
        "sec-ch-ua": "\"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"108\"",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ??????V9/2025.8.7 Chrome/108.0.5359.215 Electron/22.3.3 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://qx.car388.com/pinpai_list.php",
        "Accept-Language": "zh-CN"
    }
    cookies = {
        "qx666_2132_saltkey": "y9cti5LC",
        "qx666_2132_lastvisit": "1769496164",
        "__utmz": "139703073.1769500252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
        "__utma": "139703073.1164173733.1769500252.1769502953.1770374162.3",
        "PHPSESSID": "vaii290esqsv38ocn8kpoc61l5",
        "qx666_2132_sid": "dPBvBv"
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
            cursor.execute("SELECT * from pp_table where list_type_2 = 1 and pp_id not in (select distinct pp_id from changyi_chex) limit 1")
            rows = cursor.fetchall()
            for i in rows:
                pp_id = i['pp_id']
                pp_name = i['pp_name']
                params = {
                    "pinpai_id": pp_id
                }
                headers = {
                    "Host": "www.car388.com",
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) çææ±½ä¿®å¹³å°V9/2025.8.7 Chrome/108.0.5359.215 Electron/22.3.3 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Dest": "iframe",
                    "Referer": "https://www.car388.com/system/pC-2026/html/zlk.php?pinpai_id=39",
                    "Accept-Language": "zh-CN"
                }
                item = ChangyiChexItem()
                item['pp_id'] = pp_id
                item['pp_name'] = pp_name
                yield scrapy.Request(
                    url='https://www.car388.com/system/pC-2026/html/chex_list.php?' + urllib.parse.urlencode(params),
                    method='GET',
                    headers=headers,
                    cookies=self.cookies,
                    callback=self.parse,
                    meta={'item': item},
                )

    def parse(self, response):
        '''
        获取brand_id
        :param response:
        :return:
        '''
        response_text = unquote(response.text)
        brand_id = re.search('"brand_id":"(\d+)"', response_text).group(1)
        data = {
            "ac": "series_list",
            "brand_id": brand_id
        }
        yield scrapy.FormRequest(
            url=self.start_urls[0],
            method='POST',
            headers=self.headers,
            cookies=self.cookies,
            formdata=data,
            callback=self.parse_1,
            meta={'item':response.meta['item']},
        )

    def parse_1(self, response):
        '''
        选择车系页
        :param response:
        :return:
        '''
        # print(response.text)
        for i in response.json()['data']:
            item = copy.deepcopy(response.meta['item'])
            item['series'] = i['series']
            data = {
                "ac": "info_list",
                "type": "info_list",
                "brand_id": i['brand_id'],
                "series_id": i['series_id'],
            }
            yield scrapy.FormRequest(
                url=self.start_urls[0],
                method='POST',
                headers=self.headers,
                cookies=self.cookies,
                formdata=data,
                callback=self.parse_2,
                meta={'item':item},
            )
            break

    def parse_2(self, response):
        '''
        选择年份页
        :param response:
        :return:
        '''
        # print(response.text)
        def flatten_leaves(data):
            result = []
            for item in data:
                if item.get('children'):  # 非空 children 才递归
                    result.extend(flatten_leaves(item['children']))
                else:
                    result.append(item)
            return result

        data_list = flatten_leaves(response.json()['data'])
        for i in data_list:
            item = copy.deepcopy(response.meta['item'])
            item['chex_name'] = i['model']
            item['year'] = i['model_year']
            item['list_type'] = 2
            params = {'car_id': i['car_id']}
            item['params'] = json.dumps(params, ensure_ascii=False)
            # print(item)
            yield item



