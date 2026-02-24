import re
import urllib
import scrapy



class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_dianlutu_pp_lis"

    start_urls = ["https://www.car388.com/system/PC-2026/html/pp_list.php"]

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
        yield scrapy.Request(
            url=self.start_urls[0],
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_pp_list,
        )

    def parse_pp_list(self, response):
        # print(response.text)
        # a_list = response.xpath('//div[@class="main6"]/div[position() > 1]//a[last()]')
        target_divs = response.xpath('//div[@class="main6"]/div[position() > 1]//li[.//a]')
        for div in target_divs:
        # 对每个 div，提取其内部最后一个 a 标签
        #     print(div)
            last_a_list = div.xpath('.//a')[-1]
            title = last_a_list.xpath('.//div[@class="main8p"]/text()').get()
            if not title:
                title = last_a_list.xpath('./text()').get().strip()
            href = last_a_list.xpath('./@href').get()
            id = re.search('pinpai_id=(\d+)', href).group(1)
            print(id, title)
            # break

