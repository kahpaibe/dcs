# dcs

Crappy scrapy crawler to scrape some websites.

## Requirements and usage
**Requirements**

* [python 3.10+](https://www.python.org/)
* [scrapy](https://www.scrapy.org/) for given python version (`pip install scrapy`)

**Usage**

When in root directory of the scrapy project (where `scrapy.cfg` is), run `scrapy crawl {spider_name}` and let it do its thing. For example, `scrapy crawl melonbooks`. See below for the list of available spiders.

All saved content are done in the `Resources` folder. To do a clean run again, just delete the `Resources` folder.

**Config**

Many configs relevant to the program are available in the `./spiders/{spider_name}_spider.py` files, or in `./settings.py` for scrapy-specific settings. See below for the list of available spiders.

## Spider list
| Name | Description | Status | Todo |
| ---- | ----------- | ------ | ---- |
| melonbooks | Scrape [Melonbooks](https://www.melonbooks.co.jp/) | html dump | Extract item info to a db, clean *get next url* |
| tanocstore | Scrape [TANO*C STORE](https://www.tanocstore.net/) | html dump | Extract item info to a db, filter for albums only |
| diversedirect | Scrape [Diverse Direct](https://www.diverse.direct/) | html dump | Extract item info to a db, filter for albums only |
| bookmate | Scrape [Bookmate](https://bookmate-net.com/) | html dump | Extract item info to a db |
| akibaoo | Scrape [Akibaoo](https://www.akibaoo.com/) | html dump | Extract item info to a db, "Auto next page" |
| toranoana | Scrape [Toranoana](https://ecs.toranoana.jp/) | html dump | Extract item info to a db, more suited root url |

## Notes

The code is rather messy, as this was put together fairly quickly for a very generic purpose.

## TODO

Make the code not bad.