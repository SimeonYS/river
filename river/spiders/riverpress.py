import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import RiverItem
from itemloaders.processors import TakeFirst

pattern = r'(\xa0)?'


class RiverpressSpider(scrapy.Spider):
    name = 'riverpress'
    page = 0
    start_urls = [f'https://riverbankandtrust.com/about-us/news/press-releases/P{page}']
    ITEM_PIPELINES = {
        'riverpress.pipelines.RiverPipeline': 300,
    }


    def parse(self, response):
        links_count = []
        articles = response.xpath('//li[contains(@class,"my-3 my-md-5")]')
        for article in articles:
            date = article.xpath('.//i[@class="list-date"]/text()').get()
            post_link = article.xpath('.//h4[@class="list-title"]/a/@href').getall()
            links_count.append(post_link)
            yield from response.follow_all(post_link, self.parse_post, cb_kwargs=dict(date=date))

        next_page = f'https://riverbankandtrust.com/about-us/news/press-releases/P{self.page}'
        if len(links_count) == 10:
            self.page += 10
            yield response.follow(next_page, self.parse)


    def parse_post(self, response, date):
        title = response.xpath('//h2/text()').get()
        content = response.xpath('//div[@class="col-12 col-md-8 col-xl-9 col-xxl-7 offset-xxl-1"]//text()[not (ancestor::p[@class="pagination-links"])] | //div[@class="col-12 col-md-10 offset-md-1 col-xl-8 offset-xl-2 py-5 px-lg-0"]//text() | //div[@class="col-12 py-5 px-lg-0"]//text()[not (ancestor::h2 or ancestor::p[@class="disclaimer"])]').getall()
        content = [p.strip() for p in content if p.strip()]
        content = re.sub(pattern, "", ' '.join(content))

        item = ItemLoader(item=RiverItem(), response=response)
        item.default_output_processor = TakeFirst()

        item.add_value('title', title)
        item.add_value('link', response.url)
        item.add_value('content', content)
        item.add_value('date', date)

        yield item.load_item()
