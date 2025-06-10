"""
Post processing for Melonbooks.

**Usage**
Just run this script with python. e.g. `python melonbooks_post_process.py`

**Notes**
"""


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent)) # Allow relative import

import re
from typing import  override, Optional, Literal
from bs4 import BeautifulSoup
from db_wrapper import DBWrapper, DBColumnDescription
from dataclasses import dataclass
from spiders.melonbooks_settings import RESOURCES_FOLDER_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_id_and_image_file_name_from_url
from spiders.melonbooks_spider import MelonbookSpider

# # === User parameters ===
LOG_POSTPROCESSING_PATH = RESOURCES_FOLDER_PATH / "post_processing.log"
LOG_POSTPROCESSING_PATH.parent.mkdir(parents=True, exist_ok=True) # Create folder where log file is
DO_DB_DUMP_TO_JSON = True # If true, dumps the whole db file to a json file. Preferably disabled for large db files.

# === Database description ===
DB_PATH = RESOURCES_FOLDER_PATH / "melonbooks_db.db"
DB_TABLE_NAME = "melonbooks_db"

@dataclass
class MelonbooksColumnDescription(DBColumnDescription):
    """Describes database columns."""
    product_id: str
    name: Optional[str] = None
    author_name: Optional[str] = None
    release_date: Optional[str] = None
    price: Optional[str] = None

    url: Optional[str] = None
    image_urls: Optional[str] = None # Format is ", ".join(url_list)

    description_og: Optional[str] = None
    tags: Optional[str] = None # Format is " #".join(tags_list)
    keywords: Optional[str] = None

    event: Optional[str] = None
    author_name_alt: Optional[str] = None
    authors: Optional[str] = None
    format: Optional[str] = None
    genre: Optional[str] = None
    work_type: Optional[str] = None
    
    image_file_paths: Optional[str | Literal["ERROR"]] = None # Will be "ERROR" if there is an image url but image file could not be found. Format is ", ".join(path_list)

    @override
    def get_primary_key(self) -> str:
        return "product_id"

class MelonbooksSoupParser:
    """Wraps parsing of Melonboooks product page soup."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        self.soup_raw = soup.prettify(encoding="utf-8")

        self.name = self._get_name()
        self.author_name = self._get_author_name()
        self.url, self.product_id = self._get_url_and_product_id()
        self.image_urls, self.image_file_paths = self._get_image_urls_and_paths()

        self.description_og = self._get_description_og()
        self.price = self._get_price()
        self.tags = self._get_tags()
        self.keywords = self._get_keywords()

        table_content = self._get_table_content()
        self.event = table_content.get("イベント", None)
        self.author_name_alt = table_content.get("サークル名", None)
        self.authors = table_content.get("作家名", None) # of format ", ".join(author_list)
        self.release_date = table_content.get("発行日", None)
        self.format = table_content.get("版型・メディア", None)
        self.genre = table_content.get("ジャンル", None)
        self.work_type = table_content.get("作品種別", None)

        # TODO: manage this kind of content
        # <h3 class="page-headline mb12">試聴サンプル</h3>
        # <div style="text-align: center;">
        #     <audio controls preload="none" src="https://melonbooks.akamaized.net/special/a/3/sample/213001044142c.mp3"></audio>
        # </div>

    def _get_url_and_product_id(self) -> tuple[str | None, str | None]: # Retrieve url and product id
        link_tag = self.soup.find('link', {'rel': 'canonical'})
        if not link_tag:
            return (None, None)
        if "href" not in link_tag.attrs:
            return (None, None)
        url = link_tag["href"]

        re_item_id = re.compile(r"product_id=([\w\d]*)", re.IGNORECASE) # greedy
        m = re_item_id.search(url)
        if m:
            return (url, m.group(1))
        
        return (url, None)

    def _get_description_og(self) -> str | None: # Retrieve <meta property="og:description" ...>
        meta_tag = self.soup.find('meta', {'property': 'og:description'})
        if not meta_tag or 'content' not in meta_tag.attrs:
            return None
        
        content = meta_tag['content']
        return content

    def _get_name(self) -> str | None: # Retrieve product name
        item_name_tag = self.soup.find('h1', class_='page-header')
        if not item_name_tag:
            return None
        return item_name_tag.get_text()

    def _get_author_name(self) -> str | None: # Retrieve author name
        author_name_tag = self.soup.find('p', class_='author-name')
        if not author_name_tag:
            return None
        a = author_name_tag.find('a')
        if not a:
            return None
        return a.get_text()
    
    def _get_price(self) -> str | None: # Retrieve price
        price_tag = self.soup.find('span', class_=lambda c: c and c.startswith('yen'))
        if not price_tag:
            return None
        
        price = price_tag.get_text().strip(" \n¥").replace(",", "")
        return price

    def _get_image_urls_and_paths(self) -> tuple[str | None, str | Literal["ERROR"] | None]: # Retrieve image urls and file paths. Format is ( ", ".join(url_list), ", ".join(path_list) )
        figure_tags = self.soup.select('div.slider.my-gallery figure a')

        image_urls: list[str] = [a['href'] for a in figure_tags if 'href' in a.attrs]
        if not image_urls:
            return (None, None)

        # Clean urls
        cleaned_image_urls: list[str] = []
        for image_url in image_urls:
            image_url = MelonbookSpider.RE_CLEAN_IMAGE_URL_1.sub(".jpg", image_url) # remove text after image extension
            if image_url.startswith("//"):
                image_url = "https://www." + image_url[2:]
            image_url = MelonbookSpider.RE_CLEAN_IMAGE_URL_2.sub("melonbooks.co.jp/user_data/", image_url) # redirect
            cleaned_image_urls.append(image_url)
        
        out_urls = ", ".join(cleaned_image_urls)
            
        # Verify image files
        expected_paths: list[str] = []
        for image_url in cleaned_image_urls:
            try:
                expected_path = Path(get_id_and_image_file_name_from_url(image_url)[1])
                expected_path = ITEM_IMAGE_FOLDER_PATH / expected_path
                if expected_path.exists():
                    expected_paths.append(str(expected_path.relative_to(RESOURCES_FOLDER_PATH)))
                else:
                    expected_paths.append("ERROR")
                
            except Exception:
                    expected_paths.append("ERROR")

        out_paths = ", ".join(expected_paths)
        return (out_urls, out_paths)
        
    def _get_tags(self) -> str | None: # Retrieve tags. Format is " #".join(tags_list)
        a_tags = self.soup.select('div.item-detail2 a')
        a_texts = [a.get_text(strip=True) for a in a_tags]

        if not a_texts:
            return None

        return " ".join(a_texts)

    def _get_keywords(self) -> str | None:
        meta_tag = self.soup.find('meta', {'name': 'keywords'})
        if not meta_tag or 'content' not in meta_tag.attrs:
            return None
        return meta_tag['content']

    def _get_table_content(self) -> dict[str, str]: # Retrieve data from the <table>
        table = self.soup.select_one('div.item-detail.__light div.table-wrapper table')
        if not table:
            return {}
        
        table_data: dict[str] = {}

        for row in table.find_all('tr'):
            th = row.find('th')
            td = row.find('td')

            if th and td:
                key = th.get_text(strip=True)
                a_tags = td.find_all('a')
                if a_tags:
                    values = [tag.get_text(strip=True) for tag in a_tags]
                else:
                    values = [td.get_text(strip=True)]
                values = [val for val in values if val] # clean up

                table_data[key] = ", ".join(values)
        return table_data

if __name__ == "__main__":
    txt = "===================================================\n Starting Melonbooks post processing...\n==================================================="
    print(txt)
    with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
        f.write(f'{txt}\n')


    # === Set up database columns ===
    DB_COLUMN_DESCRIPTION = MelonbooksColumnDescription(product_id="TEXT PRIMARY KEY")
    DB_COLUMN_DESCRIPTION.name = "TEXT"
    DB_COLUMN_DESCRIPTION.author_name = "TEXT"
    DB_COLUMN_DESCRIPTION.release_date = "TEXT"
    DB_COLUMN_DESCRIPTION.price = "TEXT"
    DB_COLUMN_DESCRIPTION.url = "TEXT"
    DB_COLUMN_DESCRIPTION.image_urls = "TEXT"
    DB_COLUMN_DESCRIPTION.description_og = "TEXT"
    DB_COLUMN_DESCRIPTION.tags = "TEXT"
    DB_COLUMN_DESCRIPTION.keywords = "TEXT"
    DB_COLUMN_DESCRIPTION.event = "TEXT"
    DB_COLUMN_DESCRIPTION.author_name_alt = "TEXT"
    DB_COLUMN_DESCRIPTION.authors = "TEXT"
    DB_COLUMN_DESCRIPTION.format = "TEXT"
    DB_COLUMN_DESCRIPTION.genre = "TEXT"
    DB_COLUMN_DESCRIPTION.work_type = "TEXT"
    DB_COLUMN_DESCRIPTION.image_file_paths = "TEXT"

    # === Database Init ===
    db = DBWrapper(DB_PATH, DB_TABLE_NAME, DB_COLUMN_DESCRIPTION)

    # === Process html dumps ===
    for html_file_path in ITEM_HTML_FOLDER_PATH.rglob('*.html'):
        try:
            soup: BeautifulSoup
            # Open file
            with open(html_file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, features="html.parser")
        
            parsed = MelonbooksSoupParser(soup)
            new_item = MelonbooksColumnDescription(
                product_id=parsed.product_id,
                name=parsed.name,
                author_name=parsed.author_name,

                description_og=parsed.description_og,
                price=parsed.price,
                tags=parsed.tags,
                keywords=parsed.keywords,
                
                url=parsed.url,
                image_urls=parsed.image_urls,
                image_file_paths=parsed.image_file_paths,
                event=parsed.event,
                author_name_alt=parsed.author_name_alt,
                authors=parsed.authors,
                release_date=parsed.release_date,
                format=parsed.format,
                genre=parsed.genre,
                work_type=parsed.work_type,
            )
            new_item.strip_str_fields() # clean up
    
            db.save_item(new_item)

                    
            txt = f"Processed {html_file_path}"
            print(txt)
            with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
                f.write(f'{txt}\n')

        except Exception as e:
            txt = f"Failed to process {html_file_path} ! Exception={e}"
            print(txt)
            with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
                f.write(f'{txt}\n')

    txt = "===================================================\n Post processing done !\n==================================================="
    print(txt)
    with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
        f.write(f'{txt}\n')

    if DO_DB_DUMP_TO_JSON: #Dump db to json
        db.json_dumps(str(DB_PATH.with_suffix(".json")))