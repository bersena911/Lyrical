# -*- coding: utf-8 -*-
import re

import scrapy

from lyrical.items import LyricalItem


class LyricalSpiderSpider(scrapy.Spider):
    name = 'lyrical-spider'
    allowed_domains = ['azlyrics.com']
    proxy = 'http://127.0.0.1:24000'
    start_urls = []

    def start_requests(self):
        yield scrapy.Request(
            url='https://www.azlyrics.com',
            callback=self.parse,
            meta={
                'proxy': self.proxy
            }
        )

    def parse(self, response):
        alphabet_urls = response.xpath('//a[@class="btn btn-menu"]/@href').extract()
        for url in alphabet_urls:
            yield scrapy.Request(
                url=response.urljoin(url),
                callback=self.parse_artists,
                meta={
                    'proxy': self.proxy
                }
            )

    def parse_artists(self, response):
        artists = response.xpath('//div[@class="row"]//a')
        for artist in artists:
            name = artist.xpath('./text()').extract_first()
            url = artist.xpath('./@href').extract_first()
            yield scrapy.Request(
                url=response.urljoin(url),
                callback=self.parse_albums,
                meta={
                    'proxy': self.proxy,
                    'artist': name
                }
            )

    def parse_albums(self, response):
        artist = response.meta['artist']
        album_list = response.xpath('//div[@id="listAlbum"]/*')
        album_name = 'Other Songs'
        year = None
        for album in album_list:
            if album.root.tag == 'div':
                if album.attrib.get('id'):
                    album_name = album.xpath('./b/text()').extract_first().strip('"')
                    try:
                        year = int(re.findall(r'\d+', ' '.join(album.xpath('./text()').extract()).split('(')[-1])[0])
                    except Exception:
                        pass
                else:
                    album_name = 'Other Songs'
            elif album.root.tag == 'a':
                song_name = album.xpath('./text()').extract_first()
                song_url = album.xpath('./@href').extract_first()
                lyrical_item = LyricalItem()
                lyrical_item['album'] = album_name
                lyrical_item['artist'] = artist
                lyrical_item['song'] = song_name
                lyrical_item['year'] = year
                yield scrapy.Request(
                    url=response.urljoin(song_url),
                    callback=self.parse_lyrics,
                    meta={
                        'lyrical_item': lyrical_item,
                        'proxy': self.proxy
                    }
                )

    def parse_lyrics(self, response):
        lyrical_item = response.meta['lyrical_item']
        lyric = response.xpath('//div[@class="col-xs-12 col-lg-8 text-center"]/div[5]/text()').extract()
        lyrical_item['lyric'] = lyric
        yield lyrical_item
