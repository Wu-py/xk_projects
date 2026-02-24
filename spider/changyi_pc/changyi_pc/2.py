import requests


headers = {
    "Host": "www.car388.com",
    "sec-ch-ua": "\"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"108\"",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) app/2025.8.7 Chrome/108.0.5359.215 CoreVer/22.3.3 Safari/537.36 LT-PC/Win/2201/166",
    "sec-ch-ua-platform": "\"Windows\"",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Dest": "image",
    "Referer": "https://www.car388.com/system/second/showpic_xiang.php?page=19&lei=1&aid=24713&max=619&bili=&cc=",
    "Accept-Language": "zh-CN"
}
cookies = {
    "53gid2": "17258468377003",
    "visitor_type": "old",
    "53gid0": "17258468377003",
    "53gid1": "17258468377003",
    "53uvid": "1",
    "onliner_zdfq72099103": "0",
    "_UUID_UV": "1769479948471149",
    "53revisit": "1769479966488",
    "__utmz": "139703073.1769500252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
    "Hm_lvt_decbe98a86b71fe465bb5c6a3983c4e8": "1769501690",
    "__utma": "139703073.1164173733.1769500252.1769502953.1770374162.3",
    "PHPSESSID": "mq6eq7m0s20rd1s08lo51n1qe5",
    "53kf_72099103_from_host": "www.car388.com",
    "53kf_72099103_keyword": "https%3A%2F%2Fwww.car388.com%2Fsystem%2F2019-2%2Findex.php",
    "uuid_53kf_72099103": "19249d0e5fbd54fe5c5c4eef29ddc8df",
    "53kf_72099103_land_page": "https%253A%252F%252Fwww.car388.com%252Fsystem%252FPC-2026%252Findex.php",
    "kf_72099103_land_page_ok": "1",
    "TestCookie4479639": "4479639"
}
url = "https://www.car388.com/system/second/pic_jiePX.php/3953/1/4/11400595354479639765136/24713.php"
response = requests.get(url, headers=headers, cookies=cookies, verify=False)

print(response.text)
print(response)
with open('a.jpg', 'wb') as f:
    f.write(response.content)