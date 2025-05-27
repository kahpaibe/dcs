"""
Defines a spider for Melonbooks.
"""

import scrapy
import scrapy.http
import scrapy.http.response
import scrapy.responsetypes
from .melonbooks_settings import LOG_SEARCH_PATH, LOG_ITEMS_PATH, ITEM_HTML_FOLDER_PATH, melonbooks_urls, get_id_and_image_file_name_from_url, file_path_substitution, configure_loggers

import re

# ===================================================================
# Spider definition
# ===================================================================
# === Spider definition ===
class MelonbookSpider(scrapy.Spider):
    name = "melonbooks"
    counter_items = 0
    counter_search = 0

    RE_GET_NEXT_URL_CURRENT_PAGE = re.compile(r'\&pageno=(\d*)', re.IGNORECASE)
    RE_CLEAN_IMAGE_URL_1 = re.compile(r'\.jpg.*$', re.IGNORECASE)
    RE_CLEAN_IMAGE_URL_2 = re.compile(r'melonbooks.akamaized.net/user_data/', re.IGNORECASE)

    def __init__(self, *args, **kwargs):
        # ==== Configure loggers ====
        configure_loggers()
        super().__init__(*args, **kwargs)

    async def start(self):
        global melonbooks_urls # schedule all root urls
        for url in melonbooks_urls:
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
        item_urls = response.xpath('//div[@class="item-image"]/a/@href').getall()
        if item_urls:
            for item_url in item_urls:
                full_item_url = self._get_product_url(response, item_url)
                yield scrapy.Request(full_item_url, callback=self.parse_product, errback=self.handle_error)
        
        # === Crawl for more next search page ===
        next_page_button = response.css('a.pagenavi-next::attr(href)').get() # Check if there is a NEXT button
        if next_page_button:
            next_page_url = self._get_next_url(response, next_page_button) # Construct the URL for the next page
            yield scrapy.Request(next_page_url, callback=self.parse_search_for_products, errback=self.handle_error) # Follow the URL for the next page
    
    @staticmethod
    def _get_next_url(response: scrapy.http.TextResponse, next_page_button: str) -> str:
        match1 = MelonbookSpider.RE_GET_NEXT_URL_CURRENT_PAGE.search(response.url)
        current_page_num: str
        if match1:
            current_page_num = int(match1.group(1))
            cleanedup_url = response.url.replace(f"pageno={current_page_num}", f"pageno={current_page_num + 1}")
            return cleanedup_url
    
    @staticmethod
    def _get_product_url(response: scrapy.http.TextResponse, item_url: str) -> None:
        product_url = response.urljoin(item_url)
        if "&adult_view=1" not in product_url:
            product_url += "&adult_view=1" # bypass R18 check
        return product_url
    
    def parse_product(self, response: scrapy.http.TextResponse):
        """Parse product pages for metatada"""
        if not response:
            return
        if response.status != 200:
            self.handle_error(f"Error: {response.status}...")
        
        image_urls = self._get_image_urls(response)
        image_dest_names = {}
        for img_url in image_urls:
            image_dest_names[img_url] = get_id_and_image_file_name_from_url(img_url)[1]
        # ======== Perhaps to work on it =======
        # description = self._strip_list(response.xpath('//meta[@property="og:description"]/@content').getall())
        # comment = self._strip_list(response.xpath('//div[@class="item-detail __light mt24"]//p/text()').getall())
        # tracklist = self._strip_list(response.xpath('//h3[contains(text(), "トラックリスト")]/following-sibling::div/p/text()').getall())
        # item_info_dict = self._get_item_info_dict(response)
        # out_dict = {"image_urls": image_urls, "description": description, "comment": comment, "tracklist": tracklist, "info": item_info_dict}
        # self.counter_items+=1
        # out_str = f"item {self.counter_items} {response.url}: "
        # out_str += json.dumps(out_dict, ensure_ascii=False)
        # out_str += "\n"
        # with open(LOG_ITEMS_PATH, "a+", encoding="utf-8") as f:
        #     f.write(out_str)
        
        # ======== Instead, just retrieve the page's title and save the whole page ========
        title_xpath = response.xpath('//title/text()').get()
        file_path = ITEM_HTML_FOLDER_PATH / f"{file_path_substitution(title_xpath)}.html"
        file_path.write_bytes(response.body)

        self.counter_items+=1
        with open(LOG_ITEMS_PATH, "a+", encoding="utf-8") as f:
            f.write(f"item {self.counter_items} {response.url}." + " Images ('url': 'file_name'): " + f"{image_dest_names}" + "\n")

        # scrape images too
        yield {"melonbooks_image_urls": image_urls}

    
    @staticmethod
    def _get_image_urls(response: scrapy.http.TextResponse) -> list[str]: # retrieve all urls of all item images
        image_urls = response.xpath('//div[@class="slider my-gallery"]//figure/a/@href').getall()
        cleaned_image_urls: list[str] = []
        for image_url in image_urls:
            image_url = MelonbookSpider.RE_CLEAN_IMAGE_URL_1.sub(".jpg", image_url) # remove text after image extension
            if image_url.startswith("//"):
                image_url = "https://www." + image_url[2:]
            image_url = MelonbookSpider.RE_CLEAN_IMAGE_URL_2.sub("melonbooks.co.jp/user_data/", image_url) # redirect
            cleaned_image_urls.append(image_url)
        return cleaned_image_urls

    def handle_error(self, failure):
        """Log errors"""
        self.logger.error(f"Request failed: {failure}")
    # @staticmethod
    # def _strip_list(str_list: list[str], chars: str = "\r\n\t 　") -> list[str]: # Strip each list element
    #     return [a.strip(chars) for a in str_list]
    
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
