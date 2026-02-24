import copy
import re
import urllib
from urllib.parse import urljoin

import requests
import scrapy
from twisted.web.http import urlparse


class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_xianlutu_list_fute"

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
    cookies = {
        "_UUID_UV": "1769479948471149",
        "53gid2": "17258468377003",
        "53revisit": "1769479966488",
        "__utmz": "139703073.1769500252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
        "Hm_lvt_decbe98a86b71fe465bb5c6a3983c4e8": "1769501690",
        "__utma": "139703073.1164173733.1769500252.1769502953.1770374162.3",
        "PHPSESSID": "mq6eq7m0s20rd1s08lo51n1qe5",
        "53kf_72099103_from_host": "www.car388.com",
        "53kf_72099103_keyword": "https%3A%2F%2Fwww.car388.com%2Fsystem%2F2019-2%2Findex.php",
        "uuid_53kf_72099103": "19249d0e5fbd54fe5c5c4eef29ddc8df",
        "53kf_72099103_land_page": "https%253A%252F%252Fwww.car388.com%252Fsystem%252FPC-2026%252Findex.php",
        "kf_72099103_land_page_ok": "1"
    }



    def start_requests(self):
        pp_id = '58'
        yield scrapy.Request(
            url=self.start_urls[0] + f'?pinpai_id={pp_id}',
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_chex_list,
            meta={'item':{'pp_id':pp_id}},
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
                cookies=self.cookies,
                callback=self.parse_year_list,
                meta={'item': item},
            )
            break

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
            next_url = f'https://www.car388.com/system/chex_ziliao_s.php?s4={year_id}&c_pinpai='
            # print(next_url)
            yield scrapy.Request(
                url=next_url,
                method='GET',
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_ziliao_list,
                meta={'item': item},
                dont_filter=True,
            )
            break

    def parse_ziliao_list(self, response):
        # print(response.text)

        item = copy.deepcopy(response.meta['item'])
        ziliao_href = response.xpath('//span[@class="ziliao_name"]/a[contains(text(), "线路图")]/@href').get()
        if not ziliao_href:
            print(item, '无数据')
            return
        next_url = urljoin(response.url, ziliao_href)
        # https://www.car388.com/system/second/index.php?lei=3&s4=3953&sid=blckeoipc36191ebdol9frlcn7&saiis=8105734479639&test_id=
        # print(next_url)
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            # cookies=self.cookies,
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
            cookies=self.cookies,
            callback=self.parse_caidan_show_url,
            meta={'item': item},
            dont_filter=True,
        )

    def parse_caidan_show_url(self, response):
        item = copy.deepcopy(response.meta['item'])
        url = re.search('url=(.+?)>', response.text).group(1)
        # https://www.car388.com/system/second/tree_xians_ok.php?tid=24713&pinpai_id=58
        next_url = urljoin(response.url, url)
        # next_url = 'https://www.car388.com/system/second/tree_xians_ok.php?tid=24664&pinpai_id=58'
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_caidan_show,
            meta={'item': item},
            dont_filter=True,
        )

    def parse_caidan_show(self, response):
        item = copy.deepcopy(response.meta['item'])
        url = re.search('url=(.+?)>', response.text).group(1)
        # https://www.car388.com/system/second/tree_2022.php?tid=24664&pinpai_id=58
        next_url = urljoin(response.url, url)
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_caidan,
            meta={'item': item, 'level':1},
            dont_filter=True,
        )

    def parse_caidan(self, response):
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
                    print('gggggggggggggg')
                    print(filepath)
                    print(i)
                    yield scrapy.Request(
                        url=filepath,
                        method='GET',
                        headers=self.headers,
                        cookies=self.cookies,
                        callback=self.parse_caidan,
                        meta={'item': i, 'level': response.meta['level'] + 1},
                        dont_filter=True,
                    )
                    continue
                if not max_page:
                    try:
                        rep = requests.get(filepath, headers=self.headers, cookies=self.cookies, verify=False)
                        max_page = re.search('&max=(\d+)', rep.text).group(1)
                    except Exception as e:
                        print(i, filepath, e)
                i['filepath'] = filepath.replace('showpic', 'showpic_xiang') + f'&max={max_page}'
                print(i)

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


