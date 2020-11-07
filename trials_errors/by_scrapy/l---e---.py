# -*- coding: utf-8 -*-
import scrapy


class L---e---Spider(scrapy.Spider):
    name = 'l---e---'
    # allowed_domains = ['www.l---e---.com']
    allowed_domains = ['www.zappos.com']
    # start_urls = ['https://www.l---e---.com/in/admiralpotato']
    start_urls = ['https://www.zappos.com/men-running-shoes']

    def parse(self, response):
        for product in response.css("article"):
            yield {
                "name": product.css("p[itemprop='name']::text").extract_first()
            }
