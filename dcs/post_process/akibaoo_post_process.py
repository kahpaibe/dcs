"""
Post processing for Akibaoo.

**Usage**
Just run this script with python. e.g. `python akibaoo_post_process.py`

**Notes**
"""


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent)) # Allow relative import

import re
from typing import Optional, Literal
from bs4 import BeautifulSoup
from db_wrapper import DBWrapper, DBColumnDescription
from dataclasses import dataclass
from spiders.akibaoo_settings import RESOURCES_FOLDER_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_id_and_image_file_name_from_url
import json
try:
    from typing import override
except ImportError:
    def override(func): # dummy decorator for compatibility with Python < 3.12
        return func

# # === User parameters ===
LOG_POSTPROCESSING_PATH = RESOURCES_FOLDER_PATH / "post_processing.log"
LOG_POSTPROCESSING_PATH.parent.mkdir(parents=True, exist_ok=True) # Create folder where log file is
DO_DB_DUMP_TO_JSON = False # If true, dumps the whole db file to a json file. Preferably disabled for large db files.

# === Database description ===
DB_PATH = RESOURCES_FOLDER_PATH / "akibaoo_db.db"
DB_TABLE_NAME = "akibaoo_db"

@dataclass
class AkibaooColumnDescription(DBColumnDescription):
    """Describes database columns."""
    item_id: str
    name: Optional[str] = None
    area_details: Optional[str] = None
    info_details: Optional[str] = None

    url: Optional[str] = None
    image_urls: Optional[str] = None # Format is ", ".join(url_list)
    image_file_paths: Optional[str | Literal["ERROR"]] = None # Will be "ERROR" if there is an image url but image file could not be found. Format is ", ".join(path_list)

    @override
    def get_primary_key(self) -> str:
        return "item_id"

class AkibaooSoupParser:
    """Wraps parsing of Akibaoo product page soup."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        # self.soup_raw = soup.prettify(encoding="utf-8")

        self.url, self.item_id = self._get_item_url_and_id()
        self.name = self._get_name()
        self.area_details = self._get_area_details()
        self.info_details = self._get_info_details()

        self.image_urls, self.image_file_paths = self._get_image_urls_and_paths()

    def _get_item_url_and_id(self) -> tuple[str | None, str | None] : # Retrieve url and item id
        link = self.soup.select_one('link[rel="canonical"]')
        if not link or 'href' not in link.attrs:
            return None, None
        url = f"www.akibaoo.com{link['href']}"
        m = re.search(r"\/([^\/]+)\/?$", str(link['href']), re.IGNORECASE)
        if not m:
            return url, None
        return url, m.group(1)
    
    def _get_name(self) -> str | None: # Retrieve name
        title = self.soup.select_one('title')
        if not title:
            return None
        
        return title.text.replace(" | あきばお～こく", "").strip(" \n")

    def _get_area_details(self) -> str | None: # Retrieve content of <div class="area_Detail">
        tag = self.soup.select_one('div.area_Detail')
        if not tag:
            return None
        
        detail_dict_lists: dict[str, list[str]] = {}
        for element in tag.find_all(True):
            if element.has_attr('class'):
                class_name = ' '.join(element['class'])
                text_content = element.get_text(strip=True)
                if text_content:
                    if class_name not in detail_dict_lists:
                        detail_dict_lists[class_name] = [text_content]
                    else:
                        detail_dict_lists[class_name].append(text_content)
        detail_dict: dict[str,str] = {}
        for cn in detail_dict_lists:
            detail_dict[cn] = "\n".join(detail_dict_lists[cn])
        return json.dumps(detail_dict, ensure_ascii=False, indent=None)

    def _get_info_details(self) -> str | None: # Retrieve <p class="detail_info"> info
        goods_detail_div = soup.select_one('div#goodsDetail_info.goodsDetail_info.cf')

        if goods_detail_div:
            return str(goods_detail_div)
        return None

    def _get_image_urls_and_paths(self) -> tuple[str | None, str | None]: # Retrieve image urls and expected paths. Format is (", ".join(image_urls), ", ".join(image_paths))
        img_tags = self.soup.select('img.goodsDtlImgThumb')
        if not img_tags:
            return None, None
        image_urls = [img["src"] for img in img_tags]
        if not image_urls:
            return None, None
        
        cleaned_image_urls = [f"https://www.akibaoo.com{url}" for url in image_urls]
        
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
                    
        return (", ".join(cleaned_image_urls), ", ".join(expected_paths))

if __name__ == "__main__":
    txt = "===================================================\n Starting Akibaoo post processing...\n==================================================="
    print(txt)
    with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
        f.write(f'{txt}\n')

    # === Set up database columns ===
    DB_COLUMN_DESCRIPTION = AkibaooColumnDescription(item_id="TEXT PRIMARY KEY")
    DB_COLUMN_DESCRIPTION.name = "TEXT"
    DB_COLUMN_DESCRIPTION.area_details = "TEXT"
    DB_COLUMN_DESCRIPTION.info_details = "TEXT"
    DB_COLUMN_DESCRIPTION.url = "TEXT"
    DB_COLUMN_DESCRIPTION.image_urls = "TEXT"
    DB_COLUMN_DESCRIPTION.image_file_paths = "TEXT"

    # === Database Init ===
    db = DBWrapper(str(DB_PATH), DB_TABLE_NAME, DB_COLUMN_DESCRIPTION)

    # === Process html dumps ===
    for html_file_path in ITEM_HTML_FOLDER_PATH.rglob('*.html'):
        try:
            soup: BeautifulSoup
            # Open file
            with open(html_file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, features="html.parser")
        
            parsed = AkibaooSoupParser(soup)
            new_item = AkibaooColumnDescription(
                item_id=parsed.item_id,
                url=parsed.url,
                name=parsed.name,
                area_details=parsed.area_details,
                info_details=parsed.info_details,
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