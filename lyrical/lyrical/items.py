import scrapy


class LyricalItem(scrapy.Item):
    artist = scrapy.Field()
    album = scrapy.Field()
    year = scrapy.Field()
    song = scrapy.Field()
    lyric = scrapy.Field()
