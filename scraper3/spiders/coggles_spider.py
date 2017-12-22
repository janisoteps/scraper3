import scrapy
from scrapy.selector import Selector
from scraper3.items import CogglesItem
import hashlib
import re

class CogglesSpider(scrapy.Spider):
    name = "coggles_spider"

    # The main start function which initializes the scraping URLs and triggers parse function
    def start_requests(self):
        urls = [
            # 'https://www.coggles.com/man/view-all.list?pageNumber=1',
            'https://www.coggles.com/woman/view-all.list?pageNumber=1'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        # The response is a single html file with several sets, need to have xpath selector that is common for all sets
        products = Selector(response).xpath('.//div[contains(@class, "item-health-beauty")]')
        # print(products)
        for product in products:

            # Write out xpath and css selectors for all fields to be retrieved
            item = CogglesItem()
            NAME_SELECTOR = 'normalize-space(.//p[@class = "product-name"]/a/text())'
            PRICE_SELECTOR = 'normalize-space(.//div[@class = "price"]/span/text())'
            PRODURL_SELECTOR = './/div[@class = "line list-item-details"]/div/a/@href'
            IMAGE_SELECTOR = 'img ::attr(src)'

            # Assemble the item object which will be passed then to pipeline
            item['name'] = product.xpath(NAME_SELECTOR).extract_first()
            item['price'] = product.xpath(PRICE_SELECTOR).re('[.0-9]+')
            item['prod_url'] = product.xpath(PRODURL_SELECTOR).extract_first()
            item['image_urls'] = product.css(IMAGE_SELECTOR).extract()

            # Calculate SHA1 hash of image URL to make it easy to find the image based on hash entry and vice versa
            # Add the hash to item
            img_string = product.css(IMAGE_SELECTOR).extract_first()
            hash_object = hashlib.sha1(img_string.encode('utf8'))
            hex_dig = hash_object.hexdigest()
            item['image_hash'] = hex_dig

            yield item

        # Find the total page count, then calculate the nr of the next page, then assemble next page URL
        PAGE_COUNT_SELECTOR = './/div[@class = "pagination_pageNumbers"]/a[last()]/text()'
        page_count = int(response.xpath(PAGE_COUNT_SELECTOR).extract_first())
        next_page_nr = int(re.match('.*?([0-9]+)$', response.url).group(1)) + 1
        next_page_url = response.url.rstrip("1234567890")+str(next_page_nr)
        print('page count: '+str(page_count))
        print('next page nr: ' + str(next_page_nr))

        if next_page_nr < page_count:
            yield scrapy.Request(
                next_page_url,
                callback=self.parse
            )
