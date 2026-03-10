import base64
import time

import requests


from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath

from charset_normalizer import from_bytes


def get_filename_from_url(url):
    # 1. 解析 URL 获取路径
    parsed_path = urlparse(url).path

    # 2. 使用 PurePosixPath 处理路径 (因为 URL 总是使用正斜杠 /)
    p = PurePosixPath(parsed_path)

    # 获取完整文件名
    full_filename = p.name
    # 结果: CF.svg

    # 获取不带后缀的文件名
    stem = p.stem
    # 结果: CF

    # 获取后缀 (包含点)
    suffix = p.suffix
    # 结果: .svg

    # print(f"完整文件名: {full_filename}")
    # print(f"主文件名: {stem}")
    # print(f"后缀: {suffix}")
    return full_filename, suffix


_upload_session: requests.Session | None = None


def _get_upload_session() -> requests.Session:
    global _upload_session
    if _upload_session is None:
        session = requests.Session()
        session.headers.update({"Connection": "keep-alive"})
        _upload_session = session
    return _upload_session


def upload_file_to_oss(content, file_name, prefix="crawler", max_retries: int = 3, retry_delay: float = 2.0):
    payload = {"filename": file_name, "content": content, "prefix": prefix}
    headers = {"content-type": "application/json"}
    url = "https://h5.mythinkcar.com/fcrm-api/third_service/upload-file-by-crawler"

    session = _get_upload_session()

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(url, json=payload, headers=headers, timeout=60)
            data = resp.json()

            if data.get("code") == 0:
                data["data"] = unquote(data["data"])
                print("上传成功，URL:", data["data"])
                return True, data["data"]
            else:
                last_error = data.get("msg", "未知错误")
                print(f"第{attempt}次上传失败：", last_error)
        except requests.RequestException as e:
            last_error = str(e)
            print(f"第{attempt}次上传异常：", last_error)

        if attempt < max_retries:
            time.sleep(retry_delay)

    print("上传最终失败：", last_error)
    return False, None

def get_response_encodeing(response):
    results = from_bytes(response.content)
    if results.best():
        print(results.best().encoding)
        return results.best().encoding

if __name__ == '__main__':
    # r = requests.get('http://www.baidu.com/img/flexible/logo/pc/result.png')
    # content = base64.b64encode(r.content).decode()
    # upload_file_to_oss(content, "test.png")

    # r = requests.get('http://localhost:8000/manual/ewd/contents/overall/pdf/25.pdf')
    # content = base64.b64encode(r.content).decode()
    # upload_file_to_oss(content, "test.pdf", 'cl_ft')

    # r = requests.get('https://xingka-car-data.oss-cn-shenzhen.aliyuncs.com/crawler%2F2026-03-10%2Ftest.png')
    # with open('test.png', 'wb') as f:
    #     # 得解码
    #     f.write(base64.b64decode(r.content))

    r = requests.get('http://localhost:8000/system/css/global.css')
    encding = get_response_encodeing(r)
    # print(content)
    print(r.encoding)
    upload_file_to_oss(r.content.decode(encding), "test.css")
    #
    r = requests.get('https://xingka-car-data.oss-cn-shenzhen.aliyuncs.com/crawler/2026-03-10/test.css')
    print(r.encoding)
    print(r.headers)
    # print(r.content.decode('ISO-8859-1'))