# Scrapy settings for dcs project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html*
from pathlib import Path
import logging

BOT_NAME = "dcs"

SPIDER_MODULES = ["dcs.spiders"]
NEWSPIDER_MODULE = "dcs.spiders"

ADDONS = {}

DOWNLOADER_CLIENT_TLS_CIPHERS = ':HIGH:!DH:!aNULL' #Will solve OpenSSL.SSL.Error: [('SSL routines', '', 'dh key too small')]

# Autothrottle configuration
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5
DOWNLOAD_DELAY = 2.5

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "dcs (+http://www.yourdomain.com)"

# Crawling config
ROBOTSTXT_OBEY = False
REDIRECT_ENABLED = True
RETRY_ENABLED = True
RETRY_TIMES = 5  # Retry a failed request
DOWNLOAD_TIMEOUT = 15

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "dcs.pipelines.MelonbooksImagePipeline": 1,
    "dcs.pipelines.TanocstoreImagePipeline": 1,
    "dcs.pipelines.DiversedirectImagePipeline": 1,
    "dcs.pipelines.BookmateImagePipeline": 1,
    "dcs.pipelines.AkibaooImagePipeline": 1,
    "dcs.pipelines.ToranoanaImagePipeline": 1,
    "dcs.pipelines.SurugayaImagePipeline": 1,
                  }
# IMAGES_STORE =  # Will be overriden anyway

# Configure logger
LOG_ENABLED = True
LOG_FILE = Path(__file__).parent / "Resources" / "root_logger.log"
LOG_ENCODING = "utf-8"
LOG_FILE_APPEND = True
LOG_LEVEL = logging.DEBUG # Default logging level
LOG_SHORT_NAMES = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "dcs.middlewares.DcsSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "dcs.middlewares.DcsDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}


# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
