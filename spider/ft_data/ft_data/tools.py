import base64
import time
from concurrent.futures import ThreadPoolExecutor

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
_upload_executor: ThreadPoolExecutor | None = None


def _get_upload_session() -> requests.Session:
    global _upload_session
    if _upload_session is None:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,   # 与 host 数相关，一般保持默认即可
            pool_maxsize=20        # 每个 host 最多保留的连接数，建议 >= 16
        )
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.headers.update({"Connection": "keep-alive"})
        _upload_session = session
    return _upload_session


def _get_upload_executor() -> ThreadPoolExecutor:
    """
    后台上传使用的线程池，避免阻塞 Scrapy 的 reactor 线程。
    """
    global _upload_executor
    if _upload_executor is None:
        # 根据你的并发情况可以适当调大 / 调小
        _upload_executor = ThreadPoolExecutor(max_workers=16)
    return _upload_executor


def upload_file_to_oss(content, file_name, prefix="crawler", max_retries: int = 5, retry_delay: float = 2.0):
    payload = {"filename": file_name, "content": content, "prefix": prefix}
    headers = {"content-type": "application/json"}
    url = "https://h5.mythinkcar.com/fcrm-api/third_service/upload-file-by-crawler"

    session = _get_upload_session()

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(url, json=payload, headers=headers, timeout=30)
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


def upload_file_to_oss_async(content, file_name, prefix="crawler", max_retries: int = 3, retry_delay: float = 2.0):
    """
    异步（后台线程）上传文件到 OSS，不阻塞调用方。

    返回值为 concurrent.futures.Future；如果你不关心结果，可以直接忽略。
    """
    executor = _get_upload_executor()
    # 把同步上传任务丢到线程池里执行
    return executor.submit(upload_file_to_oss, content, file_name, prefix, max_retries, retry_delay)

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

    # r = requests.get('http://127.0.0.1:8000/manual/ewd/contents/connector/figsvg/G926A-47010.svg')
    r = requests.get('http://127.0.0.1:8000/manual/ewd/contents/connector/figsvg/G926A-47010.svg')
    content = base64.b64encode(r.content).decode()
    upload_file_to_oss(content, "test.svg")
    # upload_file_to_oss_async(r.content.decode(encding), "test.css")
    #
    # r2 = requests.get('https://xingka-car-data.oss-cn-shenzhen.aliyuncs.com/crawler/2026-03-11/test.svg')
    # print(r2.text)

    #
    # r = requests.get('https://xingka-car-data.oss-cn-shenzhen.aliyuncs.com/crawler/2026-03-10/test.css')
    # print(r.encoding)
    # print(r.headers)
    # print(r.content.decode('ISO-8859-1'))