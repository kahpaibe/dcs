# dcs

Crappy scrapy crawler to scrape some websites.

# Requirements and usage
**Requirements**

* [python 3.10+](https://www.python.org/)
* [scrapy](https://www.scrapy.org/) for given python version (`pip install scrapy`)

**Usage**

When in root directory of the scrapy project (where `scrapy.cfg` is, run `scrapy crawl melonbooks`) and let it do its thing.

All saved content are done in the `Resources` folder. To do a clean run again, just delete the `Resources` folder.

**Config**

Many configs relevant to the program are available in the `./spiders/melonbooks_spider.py` file, or in `./settings.py` for scrapy-specific settings.

# Notes

The code is rather messy, as this was put together fairly quickly for a very generic purpose.

# TODO

Make the code not bad.