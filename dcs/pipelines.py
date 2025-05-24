# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from scrapy import Request, Spider
from scrapy.crawler import Crawler
from scrapy.settings import Settings
from scrapy.http import Response
from scrapy.pipelines.images import ImagesPipeline
from scrapy.pipelines.media import MediaPipeline
from typing import Any
from typing import Callable
from .spiders import melonbooks_settings as sms
from .spiders import tanocstore_settings as sts

class MelonbooksItemImagePipeline(ImagesPipeline):
    counter = 0
    DEFAULT_IMAGES_URLS_FIELD = "melonbooks_image_urls"
    DEFAULT_IMAGES_RESULT_FIELD = "melonbooks_images"

    def __init__(
        self,
        store_uri: Any,
        download_func: Callable[[Request, Spider], Response] | None = None,
        settings: Settings | dict[str, Any] | None = None,
        *,
        crawler: Crawler | None = None,
    ):
        # Ignore store_uri (=IMAGES_STORE), using custom path instead
        super().__init__(sms.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)
            
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        item_id, file_name = sms.get_id_and_image_file_name_from_url(request.url)
        self.counter += 1
        with open(sms.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")

        return file_name
    
    
class TanocstoreItemImagePipeline(ImagesPipeline):
    counter = 0
    DEFAULT_IMAGES_URLS_FIELD = "tanocstore_image_urls"
    DEFAULT_IMAGES_RESULT_FIELD = "tanocstore_images"

    def __init__(
        self,
        store_uri: Any,
        download_func: Callable[[Request, Spider], Response] | None = None,
        settings: Settings | dict[str, Any] | None = None,
        *,
        crawler: Crawler | None = None,
    ):
        # Ignore store_uri (=IMAGES_STORE), using custom path instead
        super().__init__(sts.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)
            
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        item_id, file_name = sts.get_id_and_image_file_name_from_url(request.url)
        self.counter += 1
        with open(sts.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")

        return file_name