"""
Defines a spider for Bookmate.
"""

import scrapy
import scrapy.http
import scrapy.http.response
import scrapy.responsetypes
from .bookmate_settings import configure_loggers, LOG_SEARCH_PATH, LOG_ITEMS_PATH, ITEM_HTML_FOLDER_PATH, bookmate_urls, get_image_file_name_from_url
from .common import file_path_substitution
import logging

import re

# ===================================================================
# Spider definition
# ===================================================================
# === Spider definition ===
class BookmateSpider(scrapy.Spider):
    name = "bookmate"
    counter_items = 0
    counter_search = 0
    
    RE_KEEP_IMAGE_URL_1 = re.compile(r'/s[\d\w]+_[\d\w]+\.jpg', re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        # ==== Configure loggers ====
        configure_loggers()
        super().__init__(*args, **kwargs)

    async def start(self):
        global bookmate_urls # schedule all root urls
        for url in bookmate_urls:
            yield scrapy.Request(url=url, callback=self.parse_search_for_products, errback=self.handle_error) # Well here only 1 page (main page)

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
        
        # # === Crawl to product pages ===
        item_urls = response.xpath('//div[@class="item"]/a/@href').getall()

        if item_urls:
            for item_url in item_urls:
                full_item_url = self._get_product_url(response, item_url)
                yield scrapy.Request(full_item_url, callback=self.parse_product, errback=self.handle_error)
        
        # === Crawl for more next search page === 
        next_page_button = response.xpath('//a[contains(text(), "次のページ")]/@href').get()
        if next_page_button:
            next_page_url = self._get_next_url(response, next_page_button) # Construct the URL for the next page
            yield scrapy.Request(next_page_url, callback=self.parse_search_for_products, errback=self.handle_error) # Follow the URL for the next page

    def parse_product(self, response: scrapy.http.TextResponse):
        """Parse product pages for metatada"""
        if not response:
            return
        if response.status != 200:
            self.handle_error(f"Error: {response.status}...")

        def parse_product_do(response_: scrapy.http.TextResponse):
            """Defines the parsing action to be called or not (avoid recursion by avoiding yielding a new Request object if not needed)."""
            
            # === Retrieve image urls ===
            image_urls_ = self._get_image_urls(response_)
            image_dest_names = {}
            for img_url in image_urls_:
                image_dest_names[img_url] = get_image_file_name_from_url(img_url)

            # # ======== For now, just retrieve the page's title and save the whole page ========
            title_xpath = response_.xpath('//title/text()').get()
            file_name = f"{file_path_substitution(title_xpath)}.html"
            file_path = ITEM_HTML_FOLDER_PATH / file_name
            file_path.write_bytes(response_.body)

            self.counter_items+=1
            with open(LOG_ITEMS_PATH, "a+", encoding="utf-8") as f:
                f.write(f"item {self.counter_items} {response_.url}." + " Images ('url': 'file_name'): " + f"{image_dest_names}" + "\n")

            yield {"bookmate_image_urls": image_urls_} # yield image urls if there was some
        
        if "あなたは18歳以上ですか？" in response.text: # if r18, simulate "yes" and request again (once to avoid loops !
            logger = logging.getLogger("scrapy.core.scraper")
            logger.info(f"R18 page detected ! Trying response... ({response.url})")
            with open(LOG_ITEMS_PATH, "a+", encoding="utf-8") as f:
                f.write(f"R18 page detected ! Trying response... ({response.url})\n")

            yield scrapy.FormRequest.from_response(
                response,
                formname=None,  # No specific form name needed if there's only one form
                formdata={'yes': '1'},  # Simulate the "Yes" button press
                callback=parse_product_do, 
                errback=self.handle_error
            )
        else:
            yield from parse_product_do(response) # parsing action and pass image url pointer.     

    @staticmethod
    def _get_next_url(response: scrapy.http.TextResponse, next_page_button: str) -> str:
        cleanedup_url = response.urljoin(next_page_button)
        return cleanedup_url
    
    @staticmethod
    def _get_product_url(response: scrapy.http.TextResponse, item_url: str) -> None:
        return response.urljoin(item_url)
    
    @staticmethod
    def _get_image_urls(response: scrapy.http.TextResponse) -> list[str]: # retrieve all urls of all item images
        image_urls = response.xpath('//div[@class="item-pkg"]/a/@href').getall()
        image_urls_joined: list[str] = []
        for img_url in image_urls:
            image_urls_joined.append(response.urljoin(img_url))
        return image_urls_joined
    
    def handle_error(self, failure):
        """Log errors"""
        self.logger.error(f"Request failed: {failure}")