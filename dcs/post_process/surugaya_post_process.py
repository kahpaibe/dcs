"""
Post processing for Surugaya.

**Usage**
Just run this script with python. e.g. `python surugaya_post_process.py`

**Notes**
1. This script will process the files that HAVE BEEN downloaded from `scrapy crawl surugaya`, storing data to a sqlite3 database.

Here, images are not imported to the database, however the script will check if images are all here.
- If no image on surugaya, image_file_path will be null
- If image on surugaya but image file not found in the folder, image_file_path will be "ERROR"
- If image on surugaya and image file found, image_file_path will be the path to the image.
"""


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent)) # Allow relative import

import re
from typing import  override, Optional, Literal
from bs4 import BeautifulSoup
from db_wrapper import DBWrapper, DBColumnDescription
from dataclasses import dataclass
from spiders.surugaya_settings import LOG_IMAGES_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_id_and_image_file_name_from_url, RESOURCES_FOLDER_PATH

# === User parameters ===
LOG_POSTPROCESSING_PATH = RESOURCES_FOLDER_PATH / "post_processing.log"
LOG_POSTPROCESSING_PATH.parent.mkdir(parents=True, exist_ok=True) # Create folder where log file is
DO_DB_DUMP_TO_JSON = False # If true, dumps the whole db file to a json file. Preferably disabled for large db files.

# === Database description ===
DB_PATH = RESOURCES_FOLDER_PATH / "surugaya_db.db"
DB_TABLE_NAME = "surugaya_db"

@dataclass
class SurugayaColumnDescription(DBColumnDescription):
    """Describes database columns."""
    item_id: str
    item_name: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    brand: Optional[str] = None
    catn: Optional[str] = None
    release_date: Optional[str] = None

    item_category: Optional[str] = None
    affiliation: Optional[str] = None
    quantity: Optional[str] = None
    price: Optional[str] = None

    description: Optional[str] = None
    image_file_path: Optional[str | Literal["ERROR"]] = None # Will be "ERROR" if there is an image url but image file could not be found

    @override
    def get_primary_key(self) -> str:
        return "item_id"

class SurugayaSoupParser:
    """Wraps parsing of Surugaya product page soup."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        # self.soup_raw = soup.prettify(encoding="utf-8")

        # == Info in <script> ==
        item_dict = self._get_item_script_dict()
        self.item_id = item_dict.get('item_id', None)
        self.item_category = item_dict.get('item_category', None)
        self.affiliation = item_dict.get('affiliation', None)
        self.quantity = item_dict.get('quantity', None)
        self.price = item_dict.get('price', None)

        # == Info in <script type="application/ld+json"> ==
        app_dict = self._get_script_application_dict()
        self.item_name = app_dict.get('name', None)
        self.release_date = app_dict.get('releaseDate', None)
        self.image_url = app_dict.get('image', None)
        self.url = app_dict.get('url', None)
        self.catn = app_dict.get('mpn', None)
        self.brand = app_dict.get('brand', None)

        # == Other fields ==
        self.description = self._get_description()
        self.image_file_path = self._get_image_file_path()        
    
    def _get_item_script_dict(self) -> dict[str, str | None]: # Retrieve info from <script> item var
        script_tag = self.soup.find('script', string=lambda text: text and 'var item' in text)

        # Extract the JavaScript object from the script tag
        script_content = script_tag.string

        # Use regular expressions to extract the item dictionary
        item_pattern = re.compile(r"var item = ({.*?});", re.DOTALL)
        item_match = item_pattern.search(script_content)

        if not item_match:
            return {}
        item_str = item_match.group(1)

        re_item_id = re.compile(r"'(item_id)'\s?:\s?'([^']*?)'")
        # re_item_name = re.compile(r"'(item_name)':\s?(?:htmlDecode\()?'([^']*?)'")
        re_item_category = re.compile(r"'(item_category)'\s?:\s?(?:htmlDecode\()?'([^']*?)'")
        re_affiliation = re.compile(r"'(affiliation)'\s?:\s?(?:htmlDecode\()?'([^']*?)'")
        re_quantity = re.compile(r"'(quantity)'\s?:\s?'?([^']*?)'?\n")
        re_price = re.compile(r"'(price)'\s?:\s?'?([^']*?)'?\n")

        item_dict = {}
        for match in (regex.search(item_str) for regex in (re_item_id, re_item_category, re_affiliation, re_quantity, re_price)):
            if match:
                key = match.group(1)
                value = match.group(2)
                item_dict[key] = value
        return item_dict

    def _get_script_application_dict(self) -> dict[str, str | None]: # Retrieve info from <script type="application/ld+json">
        script_application_tag = self.soup.find('script', string=lambda text: text and 'releaseDate' in text)
        if not script_application_tag:
            return {}

        # Extract the JavaScript object from the script tag
        script_content = script_application_tag.string

        # Use regular expressions to extract the item dictionary
        re_item_name = re.compile(r'"(name)"\s?:\s?"([^"]*)",')
        # re_description = re.compile(r'"(description)":\s?"([^"]*)",')
        re_release_date = re.compile(r'"(releaseDate)"\s?:\s?"([^"]*)",')
        re_image_url = re.compile(r'"(image)"\s?:\s?"([^"]*)",')
        re_url = re.compile(r'"(url)"\s?:\s?"([^"]*)",')
        # re_offers = (offers)
        re_catn = re.compile(r'"(mpn)"\s?:\s?"([^"]*)",')
        re_brand = re.compile(r'"(brand)"\s?:\s?\{([^\{\}]*?)\}', re.MULTILINE)

        info_dict = {}
        for match in (regex.search(script_content) for regex in (re_item_name, re_release_date, re_image_url, re_url, re_catn, re_brand)):
            if match:
                key = match.group(1)
                value = match.group(2)
                info_dict[key] = value.strip("\n ")
        return info_dict

    def _get_description(self) -> str | None: # Retrieve description
        note_tag = self.soup.find('p', class_='note text-break')
        if not note_tag:
            return
        
        return note_tag.get_text(separator='\n')
    
    def _get_image_file_path(self) -> str | Literal["ERROR"] | None: # Verify if image file is here
        if not self.image_url:
            return None
        
        try:
            expected_path = Path(get_id_and_image_file_name_from_url(self.image_url)[1])
            expected_path = ITEM_IMAGE_FOLDER_PATH / expected_path
            if expected_path.exists():
                return str(expected_path.relative_to(RESOURCES_FOLDER_PATH))
            else:
                return "ERROR"
            
        except Exception:
            return "ERROR"


if __name__ == "__main__":
    txt = "===================================================\n Starting Surugaya post processing...\n==================================================="
    print(txt)
    with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
        f.write(f'{txt}\n')


    # === Set up database columns ===
    DB_COLUMN_DESCRIPTION = SurugayaColumnDescription(item_id="TEXT PRIMARY KEY")
    DB_COLUMN_DESCRIPTION.item_category = "TEXT"
    DB_COLUMN_DESCRIPTION.affiliation = "TEXT"
    DB_COLUMN_DESCRIPTION.quantity = "TEXT"
    DB_COLUMN_DESCRIPTION.price = "TEXT"
    DB_COLUMN_DESCRIPTION.item_name = "TEXT"
    DB_COLUMN_DESCRIPTION.release_date = "TEXT"
    DB_COLUMN_DESCRIPTION.image_url = "TEXT"
    DB_COLUMN_DESCRIPTION.url = "TEXT"
    DB_COLUMN_DESCRIPTION.catn = "TEXT"
    DB_COLUMN_DESCRIPTION.brand = "TEXT"
    DB_COLUMN_DESCRIPTION.description = "TEXT"
    DB_COLUMN_DESCRIPTION.image_file_path = "TEXT"

    # === Database Init ===
    db = DBWrapper(DB_PATH, DB_TABLE_NAME, DB_COLUMN_DESCRIPTION)

    # === Process html dumps ===
    for html_file_path in ITEM_HTML_FOLDER_PATH.rglob('*.html'):
        try:
            soup: BeautifulSoup
            # Open file
            with open(html_file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, features="html.parser")
        
            parsed = SurugayaSoupParser(soup)
            new_item = SurugayaColumnDescription(
                item_id=parsed.item_id, 
                item_name=parsed.item_name, 
                image_url=parsed.image_url, 
                url=parsed.url, 
                brand=parsed.brand, 
                catn=parsed.catn, 
                release_date=parsed.release_date, 
                item_category=parsed.item_category, 
                affiliation=parsed.affiliation, 
                quantity=parsed.quantity, 
                price=parsed.price,
                description=parsed.description,
                image_file_path=parsed.image_file_path
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