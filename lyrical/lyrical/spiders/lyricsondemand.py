# -*- coding: utf-8 -*-
import re

import scrapy

from lyrical.items import LyricalItem


class LyricalSpiderSpider(scrapy.Spider):
    name = 'lyricsondemand'
    allowed_domains = ['lyricsondemand.com']
    proxy = 'http://127.0.0.1:24000'
    queries = '0abcdefghijklmnopqrstuvwxyz'
    start_urls = []

    def start_requests(self):
        for query in self.queries:
            yield scrapy.Request(
                url=f'https://www.lyricsondemand.com/{query}/full.html',
                callback=self.parse,
                meta={
                    # 'proxy': self.proxy
                }
            )

    def parse(self, response):
        artists = response.xpath('//div[@id="artdata"]/ul/li/a')
        for artist in artists:
            name = artist.xpath('./text()').extract_first().replace(' Lyrics', '', -1)
            url = artist.xpath('./@href').extract_first()
            yield scrapy.Request(
                url=response.urljoin(url.lower()),
                callback=self.parse_albums,
                meta={
                    # 'proxy': self.proxy,
                    'artist': name
                }
            )

    def parse_albums(self, response):
        artist = response.meta['artist']
        album_html = response.xpath('//div[@id="listAlbum"]').extract_first()
        no_album_html = response.xpath('//div[@id="artdata"]/span/a')
        if album_html:
            years = re.findall(r'\(\d{4}\)', album_html)
            album_html = album_html.replace('Other Songs', '<b>Other Songs</b>')
            for year in years:
                replaced_year = year.replace('(', '<year>').replace(')', '</year>')
                album_html = album_html.replace(year, replaced_year)
            album_html = scrapy.Selector(text=album_html)
            album_html = album_html.xpath('//div[@id="listAlbum"]/*')
            year = None
            album_name = None
            for elem in album_html:
                if elem.root.tag == 'b':
                    album_name = elem.xpath('./text()').extract_first()
                elif elem.root.tag == 'year':
                    year = elem.xpath('./text()').extract_first()
                elif elem.root.tag == 'span':
                    if elem.xpath('.//b'):
                        album_name = elem.xpath('.//b/text()').extract_first()
                        album_song_list = response.xpath('//div[@class="albmsnglst"]/span/a')
                        for song in album_song_list:
                            song_name = song.xpath('./text()').extract_first()
                            song_url = song.xpath('./@href').extract_first()
                            lyrical_item = LyricalItem()
                            lyrical_item['artist'] = artist
                            lyrical_item['album'] = album_name
                            lyrical_item['song'] = song_name
                            lyrical_item['year'] = year
                            yield scrapy.Request(
                                url=response.urljoin(song_url.lower()),
                                callback=self.parse_lyrics,
                                meta={
                                    'lyrical_item': lyrical_item,
                                    # 'proxy': self.proxy
                                }
                            )
                    else:
                        song_name = elem.xpath('./a/text()').extract_first()
                        song_url = elem.xpath('./a/@href').extract_first()
                        if song_url == '#':
                            continue
                        lyrical_item = LyricalItem()
                        lyrical_item['artist'] = artist
                        lyrical_item['album'] = album_name
                        lyrical_item['song'] = song_name
                        lyrical_item['year'] = year
                        yield scrapy.Request(
                            url=response.urljoin(song_url.lower()),
                            callback=self.parse_lyrics,
                            meta={
                                'lyrical_item': lyrical_item,
                                # 'proxy': self.proxy
                            }
                        )
        elif no_album_html:
            album_name = 'Other Songs'
            year = None
            for song in no_album_html:
                song_name = song.xpath('./text()').extract_first()
                song_url = song.xpath('./@href').extract_first()
                lyrical_item = LyricalItem()
                lyrical_item['artist'] = artist
                lyrical_item['album'] = album_name
                lyrical_item['song'] = song_name
                lyrical_item['year'] = year
                yield scrapy.Request(
                    url=response.urljoin(song_url),
                    callback=self.parse_lyrics,
                    meta={
                        'lyrical_item': lyrical_item,
                        # 'proxy': self.proxy
                    }
                )

    def parse_lyrics(self, response):
        lyrical_item = response.meta['lyrical_item']
        lyric = ' '.join(response.xpath('//div[@class="lcontent"]/text()').extract())
        lyrical_item['lyric'] = lyric
        yield lyrical_item
