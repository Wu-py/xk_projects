# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ChangyiPcItem(scrapy.Item):
    # define the fields for your item here like:
    chex_name = scrapy.Field()
    year = scrapy.Field()
    filepath = scrapy.Field()
    title_level_1 = scrapy.Field()
    index_1 = scrapy.Field()
