"""
Akibaoo a spider for tanocstore.
"""

import scrapy
import scrapy.http
import scrapy.http.response
import scrapy.responsetypes
from .toranoana_settings import configure_loggers, LOG_SEARCH_PATH, LOG_ITEMS_PATH, ITEM_HTML_FOLDER_PATH, toranoana_urls, get_id_and_image_file_name_from_url
from .common import file_path_substitution

import re

# ===================================================================
# Spider definition
# ===================================================================
# === Spider definition ===
class ToranoanaSpider(scrapy.Spider):
    name = "toranoana"
    counter_items = 0
    counter_search = 0
    
    RE_KEEP_IMAGE_URL_1 = re.compile(r'/s[\d\w]+_[\d\w]+\.jpg', re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        # ==== Configure loggers ====
        configure_loggers()
        super().__init__(*args, **kwargs)

    async def start(self):
        global toranoana_urls # schedule all root urls
        for url in toranoana_urls:
            yield scrapy.Request(url=url, callback=self.parse_search_for_products, errback=self.handle_error)
        
    def parse_search_for_products(self, response: scrapy.http.TextResponse):
        """Parse search pages.

        Yields new requests for:
            * New search pages (next page) -> self.parse_search_for_products(...)
            * Corresponding item pages -> self.parse_product(...)"""
        if not response:
            return
        if response.status != 200:
            self.handle_error(f"Error: {response.status}...")
            
        with open(LOG_SEARCH_PATH, "a+", encoding="utf-8") as f: # Log
            self.counter_search+=1
            f.write(f"search ({self.counter_search}): {response.url}\n")
        
        # === Crawl to product pages ===
        item_urls = response.xpath('//a[@class="product-list-img-inn"]/@href').getall()

        if item_urls:
            for item_url in item_urls:
                full_item_url = self._get_product_url(response, item_url)
                yield scrapy.Request(full_item_url, callback=self.parse_product, errback=self.handle_error)
        
        # === Crawl for next search page ===
        next_page_button = response.xpath('//link[@rel="next"]/@href').get() # Check if there is a NEXT button
        if next_page_button:
            next_page_url = self._get_next_url(response, next_page_button) # Construct the URL for the next page
            yield scrapy.Request(next_page_url, callback=self.parse_search_for_products, errback=self.handle_error) # Follow the URL for the next page
    
    def parse_product(self, response: scrapy.http.TextResponse):
        """Parse product pages for metatada"""
        if not response:
            return
        if response.status != 200:
            self.handle_error(f"Error: {response.status}...")
        
        # === Retrieve image urls ===
        image_urls = self._get_image_urls(response)
        image_dest_names = {}
        for img_url in image_urls:
            image_dest_names[img_url] = get_id_and_image_file_name_from_url(img_url)[1]

        # ======== For now, just retrieve the page's title and save the whole page ========
        title_xpath = response.xpath('//title/text()').get()
        file_path = ITEM_HTML_FOLDER_PATH / f"{file_path_substitution(title_xpath)}.html"
        file_path.write_bytes(response.body)

        self.counter_items+=1
        with open(LOG_ITEMS_PATH, "a+", encoding="utf-8") as f:
            f.write(f"item {self.counter_items} {response.url}." + " Images ('url': 'file_name'): " + f"{image_dest_names}" + "\n")

        # scrape images too
        yield {"toranoana_image_urls": image_urls}

    
    @staticmethod
    def _get_image_urls(response: scrapy.http.TextResponse) -> list[str]: # retrieve all urls of all item images
        image_urls = response.xpath('//div[@class="product-detail-image-thumb-item"]/@data-src').getall()
        cleaned_image_urls = image_urls
        return cleaned_image_urls

    @staticmethod
    def _get_next_url(response: scrapy.http.TextResponse, next_page_button: str) -> str:
        return response.urljoin(next_page_button)
    
    @staticmethod
    def _get_product_url(response: scrapy.http.TextResponse, item_url: str) -> None:
        return response.urljoin(item_url)
    
    def handle_error(self, failure):
        """Log errors"""
        self.logger.error(f"Request failed: {failure}")