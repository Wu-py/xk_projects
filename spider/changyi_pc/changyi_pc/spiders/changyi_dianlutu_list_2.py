import copy
import re
import urllib
from operator import index
from urllib.parse import urlencode, urlparse, unquote

import scrapy



class ChangyiDianluLisSpider(scrapy.Spider):
    '''
    劳斯莱斯
    '''
    name = "changyi_dianlutu_lis_2"

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
        # pp_id = '186'
        # pp_id = '52'
        # pp_id = '53'
        # pp_id = '35'
        # pp_id = '1'
        pp_id = '234'
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

        yield scrapy.Request(
            url='https://www.car388.com/system/pC-2026/html/chex_list.php?' + urllib.parse.urlencode(params),
            method='GET',
            headers=headers,
            cookies=self.cookies,
            callback=self.parse,
            meta={'item':{'pp_id':pp_id}},
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
            item['che_name'] = i['model']
            item['year'] = i['model_year']
            data = {
                "ac": "car_info",
                "car_id": i['car_id'],
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
            break

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
                    item['index1'] = index1
                    item['index2'] = index2
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
                print(data)
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
                break

    def parse_5_2(self, response):
        '''
        多级目录页  table_type==3
        :param response:
        :return:
        '''
        # 奔驰
        print('dddddd')
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
            break


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
        print(response.meta['item'])
        print(response.text)
        item = copy.deepcopy(response.meta['item'])
        url = response.json()['data']['url'].split('#')[0]
        new_url = 'https://qx.car388.com/' + url
        item['filepath'] = new_url
        print(item)
        yield item



