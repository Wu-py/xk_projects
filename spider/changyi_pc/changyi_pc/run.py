from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


# spider_name = 'changyi_dianlutu_pp_lis'
# spider_name = 'changyi_dianlutu_lis'
# spider_name = 'changyi_dianlutu_detail'
# spider_name = 'changyi_dianlutu_lis_2'
# spider_name = 'changyi_dianlutu_detail_2'
# spider_name = 'changyi_xianlutu_list_fute'
# spider_name = 'changyi_xianlutu_detail_fute'
# spider_name = 'changyi_chex_2'
spider_name = 'changyi_list_2'
# spider_name = 'changyi_detail_2'

# spider_name = 'changyi_chex_3'
# spider_name = 'changyi_list_3'
# spider_name = 'changyi_detail_3'

# 获取Scrapy项目的配置信息
settings = get_project_settings()

# 创建CrawlerProcess实例
process = CrawlerProcess(settings)

# 启动爬虫
process.crawl(spider_name)

# 开始运行
process.start()