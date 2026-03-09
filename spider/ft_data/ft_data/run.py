from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


# spider_name = 'ft_repair'
spider_name = 'ft_ncf'
# spider_name = 'ft_ewd'

# 获取Scrapy项目的配置信息
settings = get_project_settings()

# 创建CrawlerProcess实例
process = CrawlerProcess(settings)
# 启动爬虫
process.crawl(spider_name, directory='N0037')
# 开始运行
process.start()

