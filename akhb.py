"""
Scrape AkibaHobby
"""

import asyncio
import aiofiles
import aiohttp
import json
import re
import logging
from pathlib import Path
from aiohttp import ClientResponse
from bs4 import BeautifulSoup, NavigableString
from functools import partial
from lib.dcs_skip import KahSkipManager
from typing import Optional

from lib.dcs_lib import KahLogger, try_find_all_else_empty_get_dict, try_find_all_else_empty_get_text, try_find_else_none, decode_if_possible, callback_image_save, redirect_url
from lib.kahscrape.kahscrape import KahRatelimitedFetcher, FetcherABC

# ==================================================================
#  General setup
# ==================================================================
SHOULD_SKIP_NON_INDIE = True # if True, skip non-indies (インディーズ) items

NAME: str = "akbh"
PATH_CURRENT = Path(__file__).parent
PATH_RESOURCES = PATH_CURRENT / "Resources"
PATH_OUTPUT = PATH_RESOURCES / NAME
PATH_LOG = PATH_OUTPUT / "logger.log"
PATH_DOWNLOADED_INDEX = PATH_OUTPUT / "downloaded_index.txt"

PATH_ITEM_JSON = PATH_OUTPUT / "json"
PATH_ITEM_JSON.mkdir(parents=True, exist_ok=True)
PATH_ITEM_IMAGES = PATH_OUTPUT / "images"
PATH_ITEM_IMAGES.mkdir(parents=True, exist_ok=True)

LOGGER = KahLogger(NAME, PATH_LOG, logging.DEBUG, logging.INFO)
skipper = KahSkipManager(PATH_DOWNLOADED_INDEX, logger=LOGGER)

# ==================================================================
#  Utilities
# ==================================================================

async def get_fetcher() -> KahRatelimitedFetcher:
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10.0))
    return KahRatelimitedFetcher(session=session, logger=LOGGER, cc_min_wait_time=0.25)

def absolute_url_if(url: Optional[str], base: str) -> Optional[str]:
    if url and url.startswith("/"):
        return f"{base}{url}"
    return url

def get_stripped(key: str, d: dict, default: Optional[str] = None) -> Optional[str]:
    v = d.get(key, default)
    if isinstance(v, str):
        return v.strip()
    return v

# ==================================================================
#  Pipelines
# ==================================================================

async def onerr(
        fetcher: FetcherABC, 
        url: str, e: Exception, 
        resp: ClientResponse | None = None, 
        data: bytes | None = None
    ):
    LOGGER.warning(f"Error occurred while fetching {url}\n\tdata={f'{decode_if_possible(data)[:40]}...' if data else None}:\n\t{e=}")
    return

# //////////////////////////////////////////////////////////////
#  Item page (json)
# //////////////////////////////////////////////////////////////
async def onreq_item_page(fetcher: FetcherABC, resp: ClientResponse, data: bytes, item_handle: Optional[str] = None):
    """Item page."""
    LOGGER.info(f"Successfully fetched {resp.url}:\n\t{decode_if_possible(data)[:40]}...")
    skipper.mark_url_as_downloaded(str(resp.url))
    
    # save json
    save_file_path = PATH_ITEM_JSON / f"{item_handle}.json"
    async with aiofiles.open(save_file_path, "wb+") as f:
        await f.write(data)

    # parse for images
    content = json.loads(decode_if_possible(data))

    if "images" not in content or not isinstance(content["images"], list):
        LOGGER.critical(f"No images found in item {item_handle}: {content}")
        return
    
    image_urls = [re.sub(r"^//", "https://", img_url) for img_url in content["images"] if isinstance(img_url, str)]
    for img_url in image_urls:
        ret = skipper.should_skip_url(img_url)
        if ret is not None:
            LOGGER.info(f"Skipping fetching {img_url}: {ret}")
            continue

        image_name = re.search(r"/([^/\?]*?)(?:\?v=\d+)?$", img_url)
        if not image_name:
            LOGGER.critical(f"Cannot parse image name from URL: {img_url}")
            continue
        image_name = image_name.group(1)
        print(f"image_name: {image_name}")

        await fetcher.fetch(
            img_url,
            partial(callback_image_save, save_file_path=PATH_ITEM_IMAGES / f"{image_name}", skipper=skipper, logger=LOGGER),
            onerr
        )

# //////////////////////////////////////////////////////////////
#  Search page (json)
# //////////////////////////////////////////////////////////////
async def onreq_search_page(fetcher: FetcherABC, resp: ClientResponse, data: bytes):
    """Search page."""
    LOGGER.info(f"Successfully fetched {resp.url}:\n\t{decode_if_possible(data)[:40]}...")
    skipper.mark_url_as_downloaded(str(resp.url))

    json_data = json.loads(decode_if_possible(data))
    for item in json_data:
        if SHOULD_SKIP_NON_INDIE and item.get("type") != "インディーズ":
            LOGGER.info(f"Skipping non-indie (インディーズ) item: {item.get('title')} ({item.get('type')})")
            continue

        item_handle = item.get("handle") # Unique identifier
        if not item_handle:
            LOGGER.critical(f"Cannot find product handle in item: {item}")
            continue

        item_url = f"https://shop.akbh.jp/products/{item_handle}.js"

        ret = skipper.should_skip_url(item_url) # Skip if already downloaded
        if ret is not None:
            LOGGER.info(f"Skipping fetching {item_url}: {ret}")
            continue

        await fetcher.fetch( # Queue item
            item_url,
            partial(onreq_item_page, item_handle=item_handle),
            onerr
        )

# ==================================================================
#  Main
# ==================================================================
if __name__ == '__main__':
        
    async def main():
        fetcher = await get_fetcher()

        # === Search pages ===
        urls = (f"https://shop.akbh.jp/collections/all-products?view=lsa&sort_by=&page={page}"
            for page in range(0, 32 + 1))
        for url in urls:
            await fetcher.fetch(
                url,
                onreq_search_page,
                onerr
            )
        
        await fetcher.wait_and_close()

    asyncio.run(main())

