import re
import urllib
import scrapy



class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_dianlutu_lis"

    start_urls = ["https://www.car388.com/system/PC-2026/html/chex_list.php"]

    headers = {
        "Host": "www.car388.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) app/2025.8.7 Chrome/108.0.5359.215 CoreVer/22.3.3 Safari/537.36 LT-PC/Win/2201/166",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "iframe",
        "Referer": "https://www.car388.com/system/PC-2026/html/zlk.php?pinpai_id=242",
        "Accept-Language": "zh-CN"
    }
    cookies = {
        "visitor_type": "old",
        "53gid0": "17258468377003",
        "53gid1": "17258468377003",
        "_UUID_UV": "1769479948471149",
        "53gid2": "17258468377003",
        "53uvid": "1",
        "onliner_zdfq72099103": "0",
        "53revisit": "1769479966488",
        "__utmz": "139703073.1769500252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
        "Hm_lvt_decbe98a86b71fe465bb5c6a3983c4e8": "1769501690",
        "PHPSESSID": "u73buei540u7nts6h3sestk1r2",
        "53kf_72099103_from_host": "www.car388.com",
        "uuid_53kf_72099103": "a27dad8669ba87bf17fe05cc08d9b1db",
        "53kf_72099103_land_page": "https%253A%252F%252Fwww.car388.com%252Fsystem%252FPC-2026%252Findex.php",
        "kf_72099103_land_page_ok": "1",
        "__utma": "139703073.1164173733.1769500252.1769502953.1770374162.3",
        "__utmc": "139703073",
        "53kf_72099103_keyword": "https%3A%2F%2Fqx.car388.com%2F"
    }


    def start_requests(self):
        pp_id = '242'
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
        meta = response.meta
        li_list = response.xpath("//li[@class='main7li']")
        for li in li_list:
            chex_name = li.xpath('.//center/text()').extract_first()
            chex_href = li.xpath('./a/@href').extract_first()
            chex_id = re.search('chex_id=(\d+)', chex_href).group(1)
            # test
            # if chex_id != '3691':
            #     continue
            # print(chex_name, chex_id)

            meta['item']['chex_name'] = chex_name
            # https://www.car388.com/system/chex_ziliao_che.php?pinpai_id=242&chex_id=3706&pinpai_name&chex_name=阿维塔06
            yield scrapy.Request(
                url=chex_href,
                method='GET',
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_year_list,
                meta=meta,
            )

    def parse_year_list(self, response):
        meta = response.meta
        tr_list = response.xpath("//tr[.//a]")
        for tr in tr_list:
            year = tr.xpath('.//div[@class="STYLE6"]/font/text()').extract_first()
            year = re.search('(\d+)', year).group(1)
            year_href = tr.xpath('.//a/@href').extract_first()
            year_id = re.search('s4=(\d+)', year_href).group(1)
            meta['item']['year'] = year
            next_url = f'https://www.car388.com/system/chex_ziliao_s.php?s4={year_id}&c_pinpai='
            yield scrapy.Request(
                url=next_url,
                method='GET',
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_ziliao_list,
                meta=meta,
                dont_filter=True,
            )
            # break

    def parse_ziliao_list(self, response):
        # print(response.text)
        meta = response.meta
        ziliao_href = response.xpath('//span[@class="ziliao_name"]/a[contains(text(), "专修手册")]/@href').extract_first()
        zid = re.search('zid=(\d+)', ziliao_href).group(1)
        next_url = f'https://www.car388.com/system/second/tree.php?pinpai_id={meta["item"]["pp_id"]}&zid={zid}&azx=jili&jilid='
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_get_caidan_show_url,
            meta=meta,
            dont_filter=True,
        )

    def parse_get_caidan_show_url(self, response):
        meta = response.meta
        # https://www.car388.com/newhd0/system-aweita-20262/caidan_show_url.php?pinpai_id=242&che_nian_id=28062
        next_url = re.search('url=(.+?)>', response.text).group(1)
        print(next_url)
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_caidan_show_url,
            meta=meta,
            dont_filter=True,
        )

    def parse_caidan_show_url(self, response):
        meta = response.meta
        url = re.search('url=(.+?)>', response.text).group(1)
        # https://www.car388.com/newhd0/system-aweita-20262/07.php
        next_url = response.request.url.rsplit('/', 1)[0] + '/' + url
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_caidan,
            meta=meta,
            dont_filter=True,
        )

    def parse_caidan(self, response):
        meta = response.meta
        dianlu_html = re.search(r"d.add\(.+?','(.+?dianlu.html)'\)", response.text).group(1)
        print(dianlu_html)
        # https://www.car388.com/newhd0/system-aweita-20262/11-dianlu.html
        next_url = response.request.url.rsplit('/', 1)[0] + '/' + dianlu_html
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_circuit_manual_data_url,
            meta=meta,
            dont_filter=True,
        )

    def parse_circuit_manual_data_url(self, response):
        meta = response.meta
        circuit_manual_data = re.search('jsonUrl: "\.(/assets/data/circuit_manual_.+?\.json)"', response.text).group(1)
        # https://www.car388.com/newhd0/system-aweita-20262/assets/data/circuit_manual_P2025060279.json
        manual_code = re.search('circuit_manual_(.+)', circuit_manual_data).group(1)
        meta['item']['manual_code'] = manual_code
        next_url = response.request.url.rsplit('/', 1)[0] + circuit_manual_data
        yield scrapy.Request(
            url=next_url,
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_circuit_manual_data,
            meta=meta,
            dont_filter=True,
        )

    def parse_circuit_manual_data(self, response):
        meta = response.meta
        base_item = meta['item']  # 原始模板

        for i in response.json():
            # 递归解析，获取所有叶子节点对应的完整 item
            for complete_item in self.parse_detail(i, base_item.copy()):
                # print("Yielded item:", complete_item)
                complete_item['filepath'] = response.request.url.rsplit('/data', 1)[0] + complete_item['filepath']
                yield complete_item  # 如果你在 Scrapy 中，这里可以 yield 给 pipeline

    @staticmethod
    def parse_detail(children, base_item):
        """
        递归解析树结构，每个叶子节点生成一个完整的 item。
        base_item: 当前路径上已填充的标题信息（如 title_level1, title_level2...）
        """
        level = children['level']
        new_item = base_item.copy()  # 关键：每层都基于父级 item 创建新副本
        new_item[f'title_level{level}'] = children['title']

        childrens = children.get('children')

        if childrens:
            # 非叶子节点：继续递归子节点
            for child in childrens:
                yield from ChangyiDianluLisSpider.parse_detail(child, new_item)
        else:
            # 叶子节点：添加 filepath 并产出完整 item
            new_item['filepath'] = children['filepath']
            yield new_item


