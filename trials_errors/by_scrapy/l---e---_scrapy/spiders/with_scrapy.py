# -*- coding: utf-8 -*-
import scrapy


class WithScrapySpider(scrapy.Spider):
    name = 'l---e---'
    allowed_domains = ['www.l---e---.com']
    # allowed_domains = ['www.zappos.com']
    start_urls = ['https://www.l---e---.com/in/admiralpotato']
    # start_urls = ['https://www.zappos.com/men-running-shoes']

    def parse(self, response):
        for profile in response.css("article"):
            yield {
                "name": profile.css("h1[class='top-card-layout__title']::text").extract_first(),
                # "by": product.css("p[itemprop='brand'] span[itemprop='name']::text").extract_first(),
                # "price": product.css("p span::text").extract()[1],
                # "stars": product.css(
                #     "p span[itemprop='aggregateRating']::attr('data-star-rating')"
                # ).extract_first(),
                # "img-url": product.css(
                #     "div span img::attr('src')").extract_first()
            }
