import copy
import json
import re
import urllib
from operator import index
from urllib.parse import urlencode, urlparse, unquote

import pymysql
import scrapy

from spider.changyi_pc.changyi_pc.items import ChangyiPcListItem


class ChangyiDianluLisSpider(scrapy.Spider):
    '''
    劳斯莱斯
    '''
    name = "changyi_list_2"
    table_name = "changyi_list"
    start_urls = ["https://qx.car388.com/plugin.php?id=qssy_api:car"]
    not_data_cars = []
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
            cursor.execute("SELECT * from changyi_chex where list_type = 2 and note is null and list_key not in (select distinct list_key from changyi_list) limit 3")
            rows = cursor.fetchall()
            for i in rows:
                # print(i)
                item = ChangyiPcListItem()
                item['pp_id'] = i['pp_id']
                item['pp_name'] = i['pp_name']
                item['series'] = i['series']
                item['chex_name'] = i['chex_name']
                item['year'] = i['year']
                item['list_key'] = i['list_key']
                car_id = json.loads(i['params'])['car_id']
                data = {
                    "ac": "car_info",
                    "car_id": car_id,
                }
                yield scrapy.FormRequest(
                    url=self.start_urls[0],
                    method='POST',
                    headers=self.headers,
                    cookies=self.cookies,
                    formdata=data,
                    callback=self.parse_3,
                    meta={'item': item},
                )

    def parse_3(self, response):
        '''
        选择维修资料页
        :param response:
        :return:
        '''
        # print(response.text)
        item = copy.deepcopy(response.meta['item'])
        data_json = response.json()['data']
        car_id = data_json['car_info']['car_id']
        targets = [item for item in data_json['car_class'][0]['matched'] if item.get('part_name') in ['电路图', '维修手册/电路图']]
        if targets:
            for target in targets:
                part_id = target['part_id']
                part_type = target['part_type']
                data = {
                    "ac": "car_tab",
                    "car_id": car_id,
                    "part_id": part_id,
                    "part_type": part_type
                }
                yield scrapy.FormRequest(
                    url=self.start_urls[0],
                    method='POST',
                    headers=self.headers,
                    cookies=self.cookies,
                    formdata=data,
                    callback=self.parse_4,
                    meta={'item': item},
                )
        else:
            print(item, '无电路图数据' )
            self.not_data_cars.append(item['list_key'])

    def parse_4(self, response):
        # print(response.text)
        for i in response.json()['data']:
            item = copy.deepcopy(response.meta['item'])
            data = {
                "ac": "Doc_List",
                "table_link": i['table_link'],
                "table_name": i['table_name']
            }
            yield scrapy.FormRequest(
                url=self.start_urls[0],
                method='POST',
                headers=self.headers,
                cookies=self.cookies,
                formdata=data,
                callback=self.parse_5,
                meta={'item': item},
                dont_filter=True,
            )

    def parse_5(self, response):
        '''
        一级目录页
        :param response:
        :return:
        '''
        # print(response.text)
        response_json = response.json()
        # 大众
        if isinstance(response_json.get('data'), dict) and response_json['data'].get('table_type') == '5':
            dianlutu_item = next((i for i in response_json['data']['json'] if i['name'] == '电路图'))
            index1 = 1
            for children1 in dianlutu_item['children']:
                base_item = response.meta['item']
                id = children1['id']
                filepath = f'https://qx.car388.com/CarHtml/elsaweb/elsa/wdDoc/{id}.html?'
                index2 = 1
                for children2 in children1.get('children'):
                    item = copy.deepcopy(base_item)
                    item['title_level_1'] = children1['name']
                    item['title_level_2'] = children2['name']
                    item['filepath'] = filepath
                    item['index_1'] = index1
                    item['index_2'] = index2
                    item['type'] = '电路图'
                    index2 += 1
                    yield item
                index1 += 1
        # 劳斯莱斯
        else:
            index = 1
            level = 1
            for i in response_json['data']:
                item = copy.deepcopy(response.meta['item'])
                item[f'title_level_{level}'] = i['name']
                item[f'index_{level}'] = index
                table_type = i['table_type']
                data = {
                    "ac": "Doc_children",
                    "table_link": str(i['table_link']),
                    "table_name": str(i['table_name']),
                    "table_type": i['table_type'],
                    "direction": i['direction'],
                    "view": i['view'],
                    "menuid": i['menuid'][0] if i.get('menuid') else '',
                }
                # print(data)
                yield scrapy.FormRequest(
                    url=self.start_urls[0],
                    method='POST',
                    headers=self.headers,
                    cookies=self.cookies,
                    formdata=data,
                    callback=self.parse_6 if str(table_type) != '3' else self.parse_5_2,
                    meta={'item': item, 'level': level},
                    dont_filter=True,
                )
                index += 1
                # break

    def parse_5_2(self, response):
        '''
        多级目录页  table_type==3
        :param response:
        :return:
        '''
        # 奔驰
        # print('dddddd')
        response_json = response.json()
        level = response.meta['level'] + 1
        index = 1
        for i in response_json['data']:
            item = copy.deepcopy(response.meta['item'])
            item[f'title_level_{level}'] = i['name']
            item[f'index_{level}'] = index
            data = {
                "ac": "Doc_children",
                "table_link": str(i['table_link']),
                "table_name": str(i['table_name']),
                "table_type": str(i['table_type']),
                "direction": str(i['direction']),
                "view": i['view'],
                "menuid": i['menuid'][0] if i.get('menuid') else '',
            }
            yield scrapy.FormRequest(
                url=self.start_urls[0],
                method='POST',
                headers=self.headers,
                cookies=self.cookies,
                formdata=data,
                callback=self.parse_6,
                meta={'item': item, 'level': level},
                dont_filter=True,
            )
            index += 1
            # break


    def parse_6(self, response):
        '''
        二级目录 请求获取详情链接  table_type==9
        :param response:
        :return:
        '''
        level = response.meta['level'] + 1
        index = 1
        for i in response.json()['data']:
            item = copy.deepcopy(response.meta['item'])
            item[f'title_level_{level}'] = i['name']
            item[f'index_{level}'] = index
            data = {
                "ac": "CarViewUrl",
                "table_link": str(i['table_link']),
                "info_link": str(i['info_link']) if i.get('info_link') else '',
                "table_name": str(i['table_name']),
                "info_type": str(i['info_type']) if i.get('info_type') else '',
                "table_type": str(i['table_type']),
                "direction": str(i['direction']),
                "view": str(i['view']),
            }
            yield scrapy.FormRequest(
                url=self.start_urls[0],
                method='POST',
                headers=self.headers,
                cookies=self.cookies,
                formdata=data,
                callback=self.parse_7,
                meta={'item': item},
                dont_filter=True,
            )
            index += 1

    def parse_7(self, response):
        '''
        构建详情页链接
        :param response:
        :return:
        '''
        # print(response.meta['item'])
        # print(response.text)
        item = copy.deepcopy(response.meta['item'])
        url = response.json()['data']['url'].split('#')[0]
        new_url = 'https://qx.car388.com/' + url
        item['filepath'] = new_url
        # print(item)
        item['type'] = '电路图'
        yield item



