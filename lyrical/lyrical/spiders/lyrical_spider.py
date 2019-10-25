# -*- coding: utf-8 -*-
import re

import scrapy
from fake_useragent import UserAgent

from lyrical.items import LyricalItem


class LyricalSpiderSpider(scrapy.Spider):
    name = 'lyrical-spider'
    allowed_domains = ['azlyrics.com']
    start_urls = []
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,ka;q=0.8',
    }

    def start_requests(self):
        self.ua = UserAgent()
        self.headers['User-Agent'] = self.ua.random
        yield scrapy.Request(
            url='https://www.azlyrics.com',
            callback=self.parse,
            headers=self.headers,
            meta={
                'proxy': 'http://127.0.0.1:24000'
            }
        )

    def parse(self, response):
        alphabet_urls = response.xpath('//a[@class="btn btn-menu"]/@href').extract()
        for url in alphabet_urls[:1]:
            self.headers['User-Agent'] = self.ua.random
            yield scrapy.Request(
                url=response.urljoin(url),
                callback=self.parse_artists,
                headers=self.headers,
                meta={
                    'proxy': 'http://127.0.0.1:24000'
                }
            )

    def parse_artists(self, response):
        lyrical_item = LyricalItem()
        artists = response.xpath('//div[@class="row"]//a')
        for artist in artists[:1]:
            name = artist.xpath('./text()').extract_first()
            url = artist.xpath('./@href').extract_first()
            lyrical_item['artist'] = name
            self.headers['User-Agent'] = self.ua.random
            yield scrapy.Request(
                url=response.urljoin(url),
                callback=self.parse_albums,
                headers=self.headers,
                meta={
                    'lyrical_item': lyrical_item,
                    'proxy': 'http://127.0.0.1:24000'
                }
            )

    def parse_albums(self, response):
        lyrical_item = response.meta['lyrical_item']
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
                new_item = lyrical_item.copy()
                song_name = album.xpath('./text()').extract_first()
                song_url = album.xpath('./@href').extract_first()
                new_item['album'] = album_name
                new_item['song'] = song_name
                new_item['year'] = year
                self.headers['User-Agent'] = self.ua.random
                yield scrapy.Request(
                    url=response.urljoin(song_url),
                    callback=self.parse_lyrics,
                    headers=self.headers,
                    meta={
                        'lyrical_item': new_item,
                        'proxy': 'http://127.0.0.1:24000'
                    }
                )

    def parse_lyrics(self, response):
        lyrical_item = response.meta['lyrical_item']
        lyric = response.xpath('//div[@class="col-xs-12 col-lg-8 text-center"]/div[5]/text()').extract()
        lyrical_item['lyric'] = lyric
        yield lyrical_item
