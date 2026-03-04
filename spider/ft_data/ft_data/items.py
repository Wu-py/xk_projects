# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FtDataListItem(scrapy.Item):
    # define the fields for your item here like:
    brand = scrapy.Field()
    model = scrapy.Field()
    year = scrapy.Field()
    destination = scrapy.Field()
    type = scrapy.Field()
    title_1 = scrapy.Field()
    title_2 = scrapy.Field()
    title_3 = scrapy.Field()
    title_4 = scrapy.Field()
    title_5 = scrapy.Field()
    title_6 = scrapy.Field()
    file_id = scrapy.Field()
    car_title_key = scrapy.Field()

class FtDataDetailItem(scrapy.Item):
    # define the fields for your item here like:
    file_id = scrapy.Field()
    content = scrapy.Field()