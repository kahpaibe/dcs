"""
Post processing for Bookmate.

**Usage**
Just run this script with python. e.g. `python bookmate_post_process.py`

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
from spiders.bookmate_settings import RESOURCES_FOLDER_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_image_file_name_from_url
import json
# from spiders.melonbooks_settings import RESOURCES_FOLDER_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_id_and_image_file_name_from_url
# from spiders.melonbooks_spider import MelonbookSpider

# # === User parameters ===
LOG_POSTPROCESSING_PATH = RESOURCES_FOLDER_PATH / "post_processing.log"
LOG_POSTPROCESSING_PATH.parent.mkdir(parents=True, exist_ok=True) # Create folder where log file is
DO_DB_DUMP_TO_JSON = True # If true, dumps the whole db file to a json file. Preferably disabled for large db files.

# === Database description ===
DB_PATH = RESOURCES_FOLDER_PATH / "bookmate_db.db"
DB_TABLE_NAME = "bookmate_db"

@dataclass
class BookmateColumnDescription(DBColumnDescription):
    """Describes database columns."""
    item_id: str
    name: Optional[str] = None
    circle_name: Optional[str] = None
    artists: Optional[str] = None
    release_date: Optional[str] = None
    genre: Optional[str] = None
    keywords: Optional[str] = None

    url: Optional[str] = None
    image_urls: Optional[str] = None # Format is ", ".join(url_list)
    image_file_paths: Optional[str | Literal["ERROR"]] = None # Will be "ERROR" if there is an image url but image file could not be found. Format is ", ".join(path_list)

    descriptions: Optional[str] = None

    @override
    def get_primary_key(self) -> str:
        return "item_id"

class BookmateSoupParser:
    """Wraps parsing of Melonboooks product page soup."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        self.soup_raw = soup.prettify(encoding="utf-8")

        self.item_id = self._get_item_id()
        self.url = f"https://bookmate-net.com/ec/{self.item_id}" if self.item_id else None
        
        item_specs_dict = self._get_item_spec()
        self.name = item_specs_dict.get("商品名", None)
        self.circle_name = item_specs_dict.get("サークル", None)
        self.release_date = item_specs_dict.get("発行日", None)
        self.artists = item_specs_dict.get("作家名", None) # Format is "\n".join(artist_list)
        self.genre = item_specs_dict.get("ジャンル", None)
        self.keywords = item_specs_dict.get("ジャンル", None) # Format is "\n".join(keyword_list)

        self.descriptions = self._get_descriptions() # Format is json "{section1: [tag1, tag2, ...], section2: ...}"
        
        self.image_urls, self.image_file_paths = self._get_image_urls_and_paths()


    def _get_item_id(self) -> str | None : # Retrieve item id
        form = self.soup.select_one('div.item-detail div.push-cart form.form-horizontal')
        if not form or 'action' not in form.attrs:
            return None
        m = re.search(r"push\/([^\/]+)", form['action'], re.IGNORECASE)
        if not m:
            return None
        return m.group(1)

    def _get_item_spec(self) -> dict[str, str]: # Retrieve item-spec content
        item_specs: dict[str, str] = {}
        dl = self.soup.find('dl', class_='item-spec')
        for dt, dd in zip(dl.find_all('dt'), dl.find_all('dd')):
            field_name = dt.get_text(strip=True)
            a_tags = dd.find_all('a')
            if a_tags:
                field_value = "\n".join([a.get_text(strip=True) for a in a_tags])
            else:
                field_value = dd.get_text(separator=' ', strip=True)
            field_value, field_name = field_value.strip(" \n"), field_name.strip(" \n")
            item_specs[field_name] = field_value
        return item_specs

    def _get_descriptions(self) -> str | None: # Retrieve description in <div class="item-msg">
        sections: dict[str, list[str]] = {}
        item_msg_div = self.soup.find('div', class_='item-msg')
        current_category = None
        for child in item_msg_div.children:
            if child.name == 'h3':
                # If the child is an h3 tag, update the current category
                current_category = child.get_text(strip=True)
                sections[current_category] = []
            elif child.name in ['p', 'h4'] and current_category is not None:
                # If the child is a p or h4 tag and there is a current category, add the text to the current category
                text_content = str(child)
                sections[current_category].append(text_content)
        if not sections:
            return None
        return json.dumps(sections, ensure_ascii=False, indent=None)

    def _get_image_urls_and_paths(self) -> tuple[str | None, str | None]: # Retrieve image urls and expected paths. Format is (", ".join(image_urls), ", ".join(image_paths))
        a_tags = self.soup.select('div.item-pkg a[href]')
        if not a_tags:
            return None, None
        image_urls = [str(a['href']) for a in a_tags]
        if not image_urls:
            return None, None
        cleaned_image_urls = [f"https://bookmate-net.com{url}" for url in image_urls]
        
        expected_paths: list[str] = []
        for image_url in cleaned_image_urls:
            try:
                expected_path = Path(get_image_file_name_from_url(image_url))
                expected_path = ITEM_IMAGE_FOLDER_PATH / expected_path
                if expected_path.exists():
                    expected_paths.append(str(expected_path.relative_to(RESOURCES_FOLDER_PATH)))
                else:
                    expected_paths.append("ERROR")
                
            except Exception:
                    expected_paths.append("ERROR")


        return (", ".join(image_urls), ", ".join(expected_paths))


if __name__ == "__main__":
    txt = "===================================================\n Starting Bookmate post processing...\n==================================================="
    print(txt)
    with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
        f.write(f'{txt}\n')


    # === Set up database columns ===
    DB_COLUMN_DESCRIPTION = BookmateColumnDescription(item_id="TEXT PRIMARY KEY")

    # === Database Init ===
    db = DBWrapper(str(DB_PATH), DB_TABLE_NAME, DB_COLUMN_DESCRIPTION)

    # === Process html dumps ===
    for html_file_path in ITEM_HTML_FOLDER_PATH.rglob('*.html'):
        try:
            soup: BeautifulSoup
            # Open file
            with open(html_file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, features="html.parser")
        
            parsed = BookmateSoupParser(soup)
            new_item = BookmateColumnDescription(
                item_id=parsed.item_id,
                name=parsed.name,
                url=parsed.url,
                circle_name=parsed.circle_name,
                artists=parsed.artists,
                release_date=parsed.release_date,
                genre=parsed.genre,
                keywords=parsed.keywords,
                descriptions=parsed.descriptions,
                image_urls=parsed.image_urls,
                image_file_paths=parsed.image_file_paths,
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