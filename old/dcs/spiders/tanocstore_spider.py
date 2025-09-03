"""
Defines a spider for tanocstore.
"""

import scrapy
import scrapy.http
import scrapy.http.response
import scrapy.responsetypes
from .tanocstore_settings import configure_loggers, LOG_SEARCH_PATH, LOG_ITEMS_PATH, ITEM_HTML_FOLDER_PATH, tanocstore_urls, get_id_and_image_file_name_from_url
from .common import file_path_substitution

import re

# ===================================================================
# Spider definition
# ===================================================================
# === Spider definition ===
class TanocstoreSpider(scrapy.Spider):
    name = "tanocstore"
    counter_items = 0
    counter_search = 0
    
    RE_KEEP_IMAGE_URL_1 = re.compile(r'/s[\d\w]+_[\d\w]+\.jpg', re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        # ==== Configure loggers ====
        configure_loggers()
        super().__init__(*args, **kwargs)

    async def start(self):
        global tanocstore_urls # schedule all root urls
        for url in tanocstore_urls:
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
        item_urls = response.xpath('//div[contains(@class, "set")]//h2/a/@href').getall()

        if item_urls:
            for item_url in item_urls:
                full_item_url = self._get_product_url(response, item_url)
                yield scrapy.Request(full_item_url, callback=self.parse_product, errback=self.handle_error)
        
        # === Crawl for more next search page ===
        next_page_button = response.xpath('//li[@class="next"]/a[contains(text(), "次の50件")]/@href').get()
        if next_page_button:
            next_page_url = self._get_next_url(response, next_page_button) # Construct the URL for the next page
            yield scrapy.Request(next_page_url, callback=self.parse_search_for_products, errback=self.handle_error) # Follow the URL for the next page
    
    @staticmethod
    def _get_next_url(response: scrapy.http.TextResponse, next_page_button: str) -> str:
        return response.urljoin(next_page_button)
    
    @staticmethod
    def _get_product_url(response: scrapy.http.TextResponse, item_url: str) -> None:
        return response.urljoin(item_url)
    
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

        # # ======== For now, just retrieve the page's title and save the whole page ========
        title_xpath = response.xpath('//title/text()').get()
        file_path = ITEM_HTML_FOLDER_PATH / f"{file_path_substitution(title_xpath)}.html"
        file_path.write_bytes(response.body)

        self.counter_items+=1
        with open(LOG_ITEMS_PATH, "a+", encoding="utf-8") as f:
            f.write(f"item {self.counter_items} {response.url}." + " Images ('url': 'file_name'): " + f"{image_dest_names}" + "\n")

        # scrape images too
        yield {"tanocstore_image_urls": image_urls}

    
    @staticmethod
    def _get_image_urls(response: scrapy.http.TextResponse) -> list[str]: # retrieve all urls of all item images
        image_urls = response.xpath('//div[@class="img"]//img/@src').getall()
        cleaned_image_urls: list[str] = []
        if image_urls:
            def _do_keep_image(_url: str) -> bool: # whether to scrape, based on url
                match = TanocstoreSpider.RE_KEEP_IMAGE_URL_1.search(_url) # exclude "small" images
                if match:
                    return False 
                return True
            cleaned_image_urls = [url for url in image_urls if _do_keep_image(url)]
        return cleaned_image_urls

    def handle_error(self, failure):
        """Log errors"""
        self.logger.error(f"Request failed: {failure}")
    # @staticmethod
    # def _get_item_info_dict(response: scrapy.http.TextResponse) -> dict[str, str]: # get info at the bottom of the page
    #     # Initialize the dictionary to store the extracted information
    #     info_dict = {}

    #     # Extract information from each row in the table
    #     rows = response.xpath('//div[contains(@class, "table-wrapper")]//table//tr')

    #     for row in rows:
    #         # Extract the header (th) and data (td) for each row
    #         header = row.xpath('./th/text()').get()
    #         value = row.xpath('./td//text()').getall()
    #         href = row.xpath('./td/a/@href').get()

    #         # Store the extracted information in the dictionary
    #         if header and value:
    #             info_dict[header] = {
    #                 'value': value,
    #                 'href': href
    #             }

    #     return info_dict
