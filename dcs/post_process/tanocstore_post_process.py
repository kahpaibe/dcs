"""
Post processing for TANO*C STORE.

**Usage**
Just run this script with python. e.g. `python tanocstore_post_process.py`

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
from spiders.tanocstore_settings import RESOURCES_FOLDER_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_id_and_image_file_name_from_url

# # === User parameters ===
LOG_POSTPROCESSING_PATH = RESOURCES_FOLDER_PATH / "post_processing.log"
LOG_POSTPROCESSING_PATH.parent.mkdir(parents=True, exist_ok=True) # Create folder where log file is
DO_DB_DUMP_TO_JSON = False # If true, dumps the whole db file to a json file. Preferably disabled for large db files.

# === Database description ===
DB_PATH = RESOURCES_FOLDER_PATH / "tanocstore_db.db"
DB_TABLE_NAME = "tanocstore_db"

@dataclass
class TanocstoreColumnDescription(DBColumnDescription):
    """Describes database columns."""
    item_id: str
    name: Optional[str] = None

    description: Optional[str] = None
    artist_catalog: Optional[str] = None
    
    url: Optional[str] = None
    image_urls: Optional[str] = None # Format is ", ".join(url_list)
    image_file_paths: Optional[str | Literal["ERROR"]] = None # Will be "ERROR" if there is an image url but image file could not be found. Format is ", ".join(path_list)

    @override
    def get_primary_key(self) -> str:
        return "item_id"

class TanocstoredirectSoupParser:
    """Wraps parsing of TANO*C STORE product page soup."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        # self.soup_raw = soup.prettify(encoding="utf-8")

        self.item_id, self.url = self._get_item_id_and_url()
        self.name = self._get_name()

        self.description = self._get_description()
        
        details_dict = self._get_details()
        self.artist_catalog = details_dict.get("artist_catalog", None)
        
        self.image_urls, self.image_file_paths = self._get_image_urls_and_paths()

    def _get_item_id_and_url(self) -> tuple[str | None, str | None]:
        meta_tag = self.soup.select_one('meta[property="og:url"]')
        if not meta_tag:
            return (None, None)

        url = str(meta_tag["content"])
        m = re.search(r"/([^/]+)/$", url)
        if not m:
            return (None, None)
        return m.group(1), url

    def _get_name(self) -> str | None: # Retrieve name
        meta_tag = self.soup.select_one('meta[property="og:title"]')
        if not meta_tag:
            return None
        return str(meta_tag["content"]).replace("-TANO*C STORE", "")

    def _get_description(self) -> str | None: # Retrieve description
        meta_tag = self.soup.select_one('meta[property="og:description"]')
        if not meta_tag:
            return None

        return str(meta_tag["content"]).strip(" \n\t")

    def _get_details(self) -> dict[str, str]: # From <div class="detailr">
        div_tag = self.soup.select_one("div.detailr")
        if not div_tag:
            return {}
        
        out_dict: dict[str, str] = {}
        h2_tag = div_tag.select_one("h2")
        if h2_tag:
            out_dict["name"] = h2_tag.get_text(strip=True)
        span_tag = div_tag.select_one("span")
        if span_tag:
            out_dict["artist_catalog"] = span_tag.get_text(strip=True)
        return out_dict
        
    def _get_image_urls_and_paths(self) -> tuple[str | None, str | None]: # Retrieve image urls and expected paths. Format is (", ".join(image_urls), ", ".join(image_paths))
        img_tags = self.soup.select('div.img img')
        if not img_tags:
            return None, None
        image_urls = [str(img["src"]) for img in img_tags]
        if not image_urls:
            return None, None
        
        expected_paths: list[str] = []
        for image_url in image_urls:
            try:
                expected_path = Path(get_id_and_image_file_name_from_url(image_url)[1])
                expected_path = ITEM_IMAGE_FOLDER_PATH / expected_path
                if expected_path.exists():
                    expected_paths.append(str(expected_path.relative_to(RESOURCES_FOLDER_PATH)))
                else:
                    expected_paths.append("ERROR")
                
            except Exception:
                    expected_paths.append("ERROR")
                    
        return (", ".join(image_urls), ", ".join(expected_paths))    

if __name__ == "__main__":
    txt = "===================================================\n Starting TANO*C STORE post processing...\n==================================================="
    print(txt)
    with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
        f.write(f'{txt}\n')

    # === Set up database columns ===
    DB_COLUMN_DESCRIPTION = TanocstoreColumnDescription(item_id="TEXT PRIMARY KEY")
    DB_COLUMN_DESCRIPTION.name = "TEXT"
    DB_COLUMN_DESCRIPTION.description = "TEXT"
    DB_COLUMN_DESCRIPTION.artist_catalog = "TEXT"
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
            with open(html_file_path, "r", encoding="euc_jp") as f:
                soup = BeautifulSoup(f, features="html.parser")
        
            parsed = TanocstoredirectSoupParser(soup)
            new_item = TanocstoreColumnDescription(
                item_id=parsed.item_id,
                name=parsed.name,
                description=parsed.description,
                artist_catalog=parsed.artist_catalog,
                url=parsed.url,
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