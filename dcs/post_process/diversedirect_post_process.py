"""
Post processing for DIVERSE DIRECT.

**Usage**
Just run this script with python. e.g. `python diversedirect_post_process.py`

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
from spiders.diversedirect_settings import RESOURCES_FOLDER_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_image_file_name_from_url
import json

# # === User parameters ===
LOG_POSTPROCESSING_PATH = RESOURCES_FOLDER_PATH / "post_processing.log"
LOG_POSTPROCESSING_PATH.parent.mkdir(parents=True, exist_ok=True) # Create folder where log file is
DO_DB_DUMP_TO_JSON = False # If true, dumps the whole db file to a json file. Preferably disabled for large db files.

# === Database description ===
DB_PATH = RESOURCES_FOLDER_PATH / "diversedirect_db.db"
DB_TABLE_NAME = "diversedirect_db"

@dataclass
class DiversedirectColumnDescription(DBColumnDescription):
    """Describes database columns."""
    item_alias: str
    name: Optional[str] = None
    
    tracklist: Optional[str] = None
    name: Optional[str] = None
    tracklist: Optional[str] = None
    special_website: Optional[str] = None
    circle_name: Optional[str] = None
    catalog_number: Optional[str] = None
    release_date: Optional[str] = None
    illustrator: Optional[str] = None
    designer: Optional[str] = None
    mastering: Optional[str] = None
    producer: Optional[str] = None

    url: Optional[str] = None
    image_urls: Optional[str] = None # Format is ", ".join(url_list)
    image_file_paths: Optional[str | Literal["ERROR"]] = None # Will be "ERROR" if there is an image url but image file could not be found. Format is ", ".join(path_list)

    @override
    def get_primary_key(self) -> str:
        return "item_alias"

class DiversedirectSoupParser:
    """Wraps parsing of DIVERSE DIRECT product page soup."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        # self.soup_raw = soup.prettify(encoding="utf-8")

        self.item_alias, self.url = self._get_item_alias_and_url()
        self.name = self._get_name()
        self.tracklist = self._get_tracklist()

        self.special_website = self._get_special_website()
        self.circle_name = self._get_circle_name()
        
        info_table = self._get_info_table()
        self.catalog_number = info_table.get("Model Number", None)
        self.release_date = info_table.get("Release Date", None)
        self.illustrator = info_table.get("Illustrator", None)
        self.designer = info_table.get("Designer", None)
        self.mastering = info_table.get("Mastering", None)
        self.producer = info_table.get("Producer", None)
        
        self.image_urls, self.image_file_paths = self._get_image_urls_and_paths()

    def _get_item_alias_and_url(self) -> tuple[str | None, str | None]: # from <meta property="og:url" content="https://www.diverse.direct/diverse-system/(.+)/"/> 
        meta_tag = self.soup.select_one('meta[property="og:url"]')
        if not meta_tag:
            return (None, None)

        url = str(meta_tag["content"])
        m = re.search(r"/([^/]+)/$", url)
        if not m:
            return (None, None)
        return m.group(1), url

    def _get_name(self) -> str | None: # Retrieve name
        title = self.soup.select_one('title')
        if not title:
            return None
        return title.text.replace("DIVERSE DIRECT | ", "")

    def _get_tracklist(self) -> str | None: # Retrieve tracklist. Format is json of the dict {track_n (str): {"track_name": "...", "track_artists": "..."} }
        tracklist_tag = self.soup.select_one('div.tracklist')
        if not tracklist_tag:
            return None

        table_rows = tracklist_tag.select('table tr')
        if not table_rows:
            return None
        
        tracklist: dict = {} #TODO: handle several disc releases ?
        for row in table_rows:
            # Extract track number, name, and artist
            track_number = row.select_one('td:nth-of-type(1)')
            if track_number:
                track_number = track_number.get_text(strip=True)
                
            track_name = row.select_one('td:nth-of-type(2)')
            if track_name:
                track_name = track_name.get_text(strip=True, separator=' ').replace('-', '').strip()

            track_artist = row.select_one('td:nth-of-type(3)')
            if track_artist:
                track_artist = track_artist.get_text(strip=True)

            tracklist[track_number] = {"track_name": track_name, "track_artists": track_artist}
        return json.dumps(tracklist, ensure_ascii=False, indent=None)
        
    def _get_special_website(self) -> str | None: # Retrieve special website
        a_tag = self.soup.select_one('div:-soup-contains("Special Website") a[href]')
        if not a_tag or "href" not in a_tag.attrs:
            return None
        return str(a_tag['href'])
    
    def _get_circle_name(self) -> str | None: # Retrieve circle name
        clear_tag = self.soup.select_one('div.right.fr div.cw.clearfix')
        if not clear_tag:
            return None
        a_tags = clear_tag.select("a[href]")
        if not a_tags:
            return None
        for a_tag in a_tags:
            if ">>Item List." not in a_tag.text:
                return a_tag.text
        return None

    def _get_info_table(self) -> dict[str, str]: # Retrieve info from the table
        clear_tag = self.soup.select_one('div.right.fr dl.clearfix')
        if not clear_tag:
            return {}
        dt_tags = clear_tag.find_all('dt')
        dd_tags = clear_tag.find_all('dd')

        info_dict: dict[str,str] = {}
        for dt, dd in zip(dt_tags, dd_tags):
            field = dt.get_text(strip=True).rstrip(':')
            value = dd.get_text(strip=True)
            info_dict[field] = value
        return info_dict
        
    def _get_image_urls_and_paths(self) -> tuple[str | None, str | None]: # Retrieve image urls and expected paths. Format is (", ".join(image_urls), ", ".join(image_paths))
        img_tags = self.soup.select('img[src]')
        if not img_tags:
            return None, None
        image_urls = [str(img["src"]) for img in img_tags]
        if not image_urls:
            return None, None
        
        expected_paths: list[str] = []
        for image_url in image_urls:
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
    txt = "===================================================\n Starting DIVERSE DIRECT post processing...\n==================================================="
    print(txt)
    with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
        f.write(f'{txt}\n')


    # === Set up database columns ===
    DB_COLUMN_DESCRIPTION = DiversedirectColumnDescription(item_alias="TEXT PRIMARY KEY")
    DB_COLUMN_DESCRIPTION.name = "TEXT"
    DB_COLUMN_DESCRIPTION.tracklist = "TEXT"
    DB_COLUMN_DESCRIPTION.item_alias = "TEXT"
    DB_COLUMN_DESCRIPTION.name = "TEXT"
    DB_COLUMN_DESCRIPTION.tracklist = "TEXT"
    DB_COLUMN_DESCRIPTION.special_website = "TEXT"
    DB_COLUMN_DESCRIPTION.circle_name = "TEXT"
    DB_COLUMN_DESCRIPTION.catalog_number = "TEXT"
    DB_COLUMN_DESCRIPTION.release_date = "TEXT"
    DB_COLUMN_DESCRIPTION.illustrator = "TEXT"
    DB_COLUMN_DESCRIPTION.designer = "TEXT"
    DB_COLUMN_DESCRIPTION.mastering = "TEXT"
    DB_COLUMN_DESCRIPTION.producer = "TEXT"
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
        
            parsed = DiversedirectSoupParser(soup)
            new_item = DiversedirectColumnDescription(
                item_alias=parsed.item_alias,
                name=parsed.name,
                tracklist=parsed.tracklist,
                special_website=parsed.special_website,
                circle_name=parsed.circle_name,
                catalog_number=parsed.catalog_number,
                release_date=parsed.release_date,
                illustrator=parsed.illustrator,
                designer=parsed.designer,
                mastering=parsed.mastering,
                producer=parsed.producer,
                image_urls=parsed.image_urls,
                image_file_paths=parsed.image_file_paths,
                url=parsed.url
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