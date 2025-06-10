# dcs

Crappy scrapy crawler to scrape some websites.

## Requirements and usage
**Requirements**

* [python 3.10+](https://www.python.org/)
* [scrapy](https://www.scrapy.org/) for given python version (`pip install scrapy`)
* [sqlite3](docs.python.org/3/library/sqlite3.html) for given python version

**Usage**

When in root directory of the scrapy project (where `scrapy.cfg` is), run `scrapy crawl {spider_name}` and let it do its thing. For example, `scrapy crawl melonbooks`. See below for the list of available spiders.

All saved content are done in the `Resources` folder. To do a clean run again, just delete the `Resources` folder.

**Config**

Many configs relevant to the program are available in the `./spiders/{spider_name}_spider.py` files, or in `./settings.py` for scrapy-specific settings. See below for the list of available spiders.

## Spider list
| Name | Description | Status | Todo |
| ---- | ----------- | ------ | ---- |
| melonbooks | Scrape [Melonbooks](https://www.melonbooks.co.jp/) | html dump | Extract item info to a db, clean *get next url*, download samples for items like [here](https://www.melonbooks.co.jp/detail/detail.php?product_id=2492871), will also dump search page html for some reason |
| tanocstore | Scrape [TANO*C STORE](https://www.tanocstore.net/) | html dump | Extract item info to a db, filter for albums only |
| diversedirect | Scrape [Diverse Direct](https://www.diverse.direct/) | html dump | Extract item info to a db, filter for albums only |
| bookmate | Scrape [Bookmate](https://bookmate-net.com/) | html dump | Extract item info to a db, add support for images in description like [here](https://bookmate-net.com/ec/57252?sec=dojin) |
| akibaoo | Scrape [Akibaoo](https://www.akibaoo.com/) | html dump | Extract item info to a db, "Auto next page" |
| toranoana | Scrape [Toranoana](https://ecs.toranoana.jp/) | html dump | Extract item info to a db, more suited root url |
| surugaya | Scrape [Surugaya](https://www.suruga-ya.jp/) | html dump | |

## Post processing

Added at a later development stage, the following scripts allow parsing the already downloaded content, saving data to a [sqlite3](docs.python.org/3/library/sqlite3.html) database. 

To use them, run the respective scripts found in `post_process/{name}.py with python.


| Name | Description | Todo |
| ---- | ----------- | ------ |
| `surugaya_post_process.py` | For Surugaya | Save images in DB too |
| `melonbooks_post_process.py` | For Melonbooks | Save images in DB too, manage samples like [here](https://www.melonbooks.co.jp/detail/detail.php?product_id=2492871) |
| `bookmate_post_process.py` | For Bookmate | Extract events from 関連キーワード |
| `akibaoo_post_process.py` | For Akibaoo | Manage images in description like [here](https://www.akibaoo.com/c/80/2500020540633/), further process json blocks |



## Notes

The code is rather messy, as this was put together fairly quickly for a very generic purpose.

## TODO

Make the code not bad.