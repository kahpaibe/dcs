"""
Akibaoo a spider for tanocstore.
"""

import scrapy
import scrapy.http
import scrapy.http.response
import scrapy.responsetypes
from .surugaya_settings import configure_loggers, LOG_ITEMS_PATH, ITEM_HTML_FOLDER_PATH, surugaya_urls, get_id_and_image_file_name_from_url
from .common import file_path_substitution

import re

# ===================================================================
# Spider definition
# ===================================================================
# === Spider definition ===
class SurugayaSpider(scrapy.Spider):
    name = "surugaya"
    counter_items = 0
    counter_search = 0
    
    RE_KEEP_IMAGE_URL_1 = re.compile(r'/s[\d\w]+_[\d\w]+\.jpg', re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        # ==== Configure loggers ====
        configure_loggers()
        super().__init__(*args, **kwargs)

    def handle_error(self, failure):
        """Log errors"""
        self.logger.error(f"Request failed: {failure}")

    async def start(self):
        global surugaya_urls # schedule all root urls
        for url in surugaya_urls:
            yield scrapy.Request(url=url, callback=self.parse_product, errback=self.handle_error)
        
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
        if len(image_urls) > 0:
            yield {"surugaya_image_urls": [image_urls[0]]}


    @staticmethod
    def _get_image_urls(response: scrapy.http.TextResponse) -> list[str]: # retrieve all urls of all item images
        image_url = response.xpath('//div[@class="product_zoom"]/a/@href').get()
        if image_url:
            cleaned_image_urls = [image_url]
            return cleaned_image_urls
        return []
