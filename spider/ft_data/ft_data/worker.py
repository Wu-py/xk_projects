# worker.py
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def run_single_crawler():
    if len(sys.argv) < 2:
        print("缺少目录参数")
        return False

    directory = sys.argv[1]
    spider_name = sys.argv[2] if len(sys.argv) > 2 else 'ft_ewd'

    try:
        settings = get_project_settings()
        # 可以在这里根据 directory 修改 settings
        # settings.set('...', ...)

        process = CrawlerProcess(settings)
        process.crawl(spider_name, directory=directory)
        process.start()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == '__main__':
    success = run_single_crawler()
    sys.exit(0 if success else 1)