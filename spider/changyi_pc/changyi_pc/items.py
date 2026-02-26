# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ChangyiPcListItem(scrapy.Item):
    # define the fields for your item here like:
    pp_id = scrapy.Field()
    pp_name = scrapy.Field()
    series = scrapy.Field()
    chex_name = scrapy.Field()
    year = scrapy.Field()
    title_level_1 = scrapy.Field()
    index_1 = scrapy.Field()
    title_level_2 = scrapy.Field()
    index_2 = scrapy.Field()
    title_level_3 = scrapy.Field()
    index_3 = scrapy.Field()
    title_level_4 = scrapy.Field()
    index_4 = scrapy.Field()
    title_level_5 = scrapy.Field()
    index_5 = scrapy.Field()
    filepath = scrapy.Field()
    type = scrapy.Field()
