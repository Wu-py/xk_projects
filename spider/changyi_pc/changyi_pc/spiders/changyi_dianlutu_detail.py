import re
import urllib
from urllib.parse import urljoin

import scrapy
from lxml import etree



class ChangyiDianluLisSpider(scrapy.Spider):
    name = "changyi_dianlutu_detail"

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
            url="https://www.car388.com/newhd0/system-aweita-20262/assets/ebook/P2025060294/topics/v0-3a07634d-3cf2-4a9e-bd3f-e67dcf1f4c22.html",
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse,
        )

    def parse(self, response):
        # 将 response 转为可修改的 lxml 文档
        parser = etree.HTMLParser()
        tree = etree.fromstring(response.text, parser)

        for img in tree.xpath('//img[@src]'):
            src = img.get('src')
            if src:
                new_src = urljoin(response.url, src)
                img.set('src', new_src)
        for script in tree.xpath('//script'):
            script.getparent().remove(script)

        # 获取修改后的 HTML 字符串
        new_html = etree.tostring(tree, encoding='unicode')
        print(new_html)


