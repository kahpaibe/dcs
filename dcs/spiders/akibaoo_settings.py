"""
Defines a few useful things and the settings made for this scraping project.
"""

import re
import hashlib
import logging
from pathlib import Path
from scrapy.utils.python import to_bytes
from .common import file_path_substitution

# ===================================================================
# User settings
# ===================================================================
RESOURCES_FOLDER_PATH = Path(__file__).parent.parent / "Resources" / "AkibaooSpider"
LOG_SEARCH_PATH = RESOURCES_FOLDER_PATH / "parsed_search_pages.log" # Here will be logged all search pages parsed
LOG_ITEMS_PATH = RESOURCES_FOLDER_PATH / "parsed_item_pages.log" # Here will be logged all item pages parsed
LOG_IMAGES_PATH = RESOURCES_FOLDER_PATH / "parsed_images.log" # Here will be logged all images the program tried to download
ITEM_IMAGE_FOLDER_PATH = RESOURCES_FOLDER_PATH / "ItemImages"
ITEM_HTML_FOLDER_PATH = RESOURCES_FOLDER_PATH / "ItemPages"

def configure_loggers(): # Called when starting the spider, configure the loggers with corresponding levels.
    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.getLogger("scrapy.utils.log").setLevel(logging.INFO)
    logging.getLogger("scrapy.extensions.telnet").setLevel(logging.DEBUG)
    logging.getLogger("scrapy.core.engine").setLevel(logging.INFO)
    logging.getLogger("scrapy.dupefilters").setLevel(logging.INFO)
    logging.getLogger("scrapy.pipelines.files").setLevel(logging.INFO)
    logging.getLogger("scrapy.core.scraper").setLevel(logging.INFO)
    logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.INFO)

# ===================================================================
# root url list definition
#   Here, define the first pages to parse, from which new pages can be accessed. For example, a search pages for all M3-XX events.
# ===================================================================
akibaoo_urls: list[str] = [] # /!\ Should be updated if there are more pages !
for i in range(1,61): # Manually adding all search pages for doujin music because there is no "next page" button easily accessible
    akibaoo_urls.append(f"https://www.akibaoo.com/c/82/?page={i}") # Category for Doujin Music

# ======================================================================
# Utilities
# ======================================================================
RE_ITEM_ID_FROM_IMAGE_URL = re.compile(r'/([^/]+)\.jpg')
def get_item_id_from_image_url(url: str) -> str:
    """Retrieve item id from given url"""
    match = RE_ITEM_ID_FROM_IMAGE_URL.search(url)
    if match:
        return match.group(1)
    else:
        logging.warning(f"Warning! Could not find id in {url} !")

def get_id_and_image_file_name_from_url(url: str) -> tuple[str, str]:
    """Compute image name from url and return [id, file_name]"""
    item_id = get_item_id_from_image_url(url)
    return (item_id, file_path_substitution(f"{item_id}_{hashlib.sha1(to_bytes(url)).hexdigest()}.jpg"))


# ======================================================================
# Some inits
# ======================================================================
# === Create folders ===
LOG_SEARCH_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_ITEMS_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_IMAGES_PATH.parent.mkdir(parents=True, exist_ok=True)
ITEM_IMAGE_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
ITEM_HTML_FOLDER_PATH.mkdir(parents=True, exist_ok=True)