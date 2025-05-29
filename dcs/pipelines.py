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
from .spiders import melonbooks_settings as smbs
from .spiders import tanocstore_settings as stcs
from .spiders import diversedirect_settings as sdds
from .spiders import bookmate_settings as sbms
from .spiders import akibaoo_settings as sabs
from .spiders import toranoana_settings as stns
from .spiders import surugaya_settings as ssys

class MelonbooksImagePipeline(ImagesPipeline):
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
        super().__init__(smbs.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)

    def image_downloaded(
        self,
        response: Response,
        request: Request,
        info: MediaPipeline.SpiderInfo,
        *,
        item: Any = None,
        ) -> str:
        item_id, file_name = smbs.get_id_and_image_file_name_from_url(request.url)
        self.counter += 1
        with open(smbs.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")

        super().image_downloaded(response, request, info, item=item) 
            
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        item_id, file_name = smbs.get_id_and_image_file_name_from_url(request.url)
        return file_name
    
    
class TanocstoreImagePipeline(ImagesPipeline):
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
        super().__init__(stcs.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)

    def image_downloaded(
        self,
        response: Response,
        request: Request,
        info: MediaPipeline.SpiderInfo,
        *,
        item: Any = None,
        ) -> str:
        item_id, file_name = stcs.get_id_and_image_file_name_from_url(request.url)
        self.counter += 1
        with open(stcs.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")

        super().image_downloaded(response, request, info, item=item) 
            
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        item_id, file_name = stcs.get_id_and_image_file_name_from_url(request.url)
        return file_name
    
    
class DiversedirectImagePipeline(ImagesPipeline):
    counter = 0
    DEFAULT_IMAGES_URLS_FIELD = "diversedirect_image_urls"
    DEFAULT_IMAGES_RESULT_FIELD = "diversedirect_images"

    def __init__(
        self,
        store_uri: Any,
        download_func: Callable[[Request, Spider], Response] | None = None,
        settings: Settings | dict[str, Any] | None = None,
        *,
        crawler: Crawler | None = None,
    ):
        # Ignore store_uri (=IMAGES_STORE), using custom path instead
        super().__init__(sdds.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)

    def image_downloaded(
        self,
        response: Response,
        request: Request,
        info: MediaPipeline.SpiderInfo,
        *,
        item: Any = None,
        ) -> str:
        file_name = sdds.get_image_file_name_from_url(request.url)
        self.counter += 1
        with open(sdds.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")

        super().image_downloaded(response, request, info, item=item) 
            
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        file_name = sdds.get_image_file_name_from_url(request.url)
        return file_name
    
class BookmateImagePipeline(ImagesPipeline):
    counter = 0
    DEFAULT_IMAGES_URLS_FIELD = "bookmate_image_urls"
    DEFAULT_IMAGES_RESULT_FIELD = "bookmate_images"

    def __init__(
        self,
        store_uri: Any,
        download_func: Callable[[Request, Spider], Response] | None = None,
        settings: Settings | dict[str, Any] | None = None,
        *,
        crawler: Crawler | None = None,
    ):
        # Ignore store_uri (=IMAGES_STORE), using custom path instead
        super().__init__(sbms.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)

    def image_downloaded(
        self,
        response: Response,
        request: Request,
        info: MediaPipeline.SpiderInfo,
        *,
        item: Any = None,
        ) -> str:
        file_name = sbms.get_image_file_name_from_url(request.url)
        self.counter += 1
        with open(sbms.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")

        super().image_downloaded(response, request, info, item=item) 
            
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        file_name = sbms.get_image_file_name_from_url(request.url)
        return file_name
    
class AkibaooImagePipeline(ImagesPipeline):
    counter = 0
    DEFAULT_IMAGES_URLS_FIELD = "akibaoo_image_urls"
    DEFAULT_IMAGES_RESULT_FIELD = "akibaoo_images"

    def __init__(
        self,
        store_uri: Any,
        download_func: Callable[[Request, Spider], Response] | None = None,
        settings: Settings | dict[str, Any] | None = None,
        *,
        crawler: Crawler | None = None,
    ):
        # Ignore store_uri (=IMAGES_STORE), using custom path instead
        super().__init__(sabs.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)

    def image_downloaded(
        self,
        response: Response,
        request: Request,
        info: MediaPipeline.SpiderInfo,
        *,
        item: Any = None,
        ) -> str:
        file_name = sabs.get_id_and_image_file_name_from_url(request.url)[1]
        self.counter += 1
        with open(sabs.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")

        super().image_downloaded(response, request, info, item=item) 
            
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        file_name = sabs.get_id_and_image_file_name_from_url(request.url)[1]
        return file_name
    
    
class ToranoanaImagePipeline(ImagesPipeline):
    counter = 0
    DEFAULT_IMAGES_URLS_FIELD = "toranoana_image_urls"
    DEFAULT_IMAGES_RESULT_FIELD = "toranoana_images"

    def __init__(
        self,
        store_uri: Any,
        download_func: Callable[[Request, Spider], Response] | None = None,
        settings: Settings | dict[str, Any] | None = None,
        *,
        crawler: Crawler | None = None,
    ):
        # Ignore store_uri (=IMAGES_STORE), using custom path instead
        super().__init__(stns.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)

    def image_downloaded(
        self,
        response: Response,
        request: Request,
        info: MediaPipeline.SpiderInfo,
        *,
        item: Any = None,
        ) -> str:
        file_name = stns.get_id_and_image_file_name_from_url(request.url)[1]
        self.counter += 1
        with open(stns.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")

        super().image_downloaded(response, request, info, item=item) 

    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        file_name = stns.get_id_and_image_file_name_from_url(request.url)[1]
        return file_name
    
class SurugayaImagePipeline(ImagesPipeline):
    counter = 0
    DEFAULT_IMAGES_URLS_FIELD = "surugaya_image_urls"
    DEFAULT_IMAGES_RESULT_FIELD = "surugaya_images"

    def __init__(
        self,
        store_uri: Any,
        download_func: Callable[[Request, Spider], Response] | None = None,
        settings: Settings | dict[str, Any] | None = None,
        *,
        crawler: Crawler | None = None,
    ):
        # Ignore store_uri (=IMAGES_STORE), using custom path instead
        super().__init__(ssys.ITEM_IMAGE_FOLDER_PATH, download_func, settings, crawler=crawler)
            
    def image_downloaded(
        self,
        response: Response,
        request: Request,
        info: MediaPipeline.SpiderInfo,
        *,
        item: Any = None,
    ) -> str:
        file_name = ssys.get_id_and_image_file_name_from_url(request.url)[1]
        self.counter += 1
        with open(ssys.LOG_IMAGES_PATH, "+a", encoding="utf-8") as f:
            f.write(f"image {self.counter}: {request.url} (saved as {file_name})\n")
        
        super().image_downloaded(response, request, info, item=item)
        
    def file_path(
        self,
        request: Request,
        response: Response | None = None,
        info: MediaPipeline.SpiderInfo | None = None,
        *,
        item: Any = None,
    ) -> str:
        file_name = ssys.get_id_and_image_file_name_from_url(request.url)[1]
        return file_name