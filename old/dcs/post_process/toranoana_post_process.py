"""
Post processing for Toranoana.

**Usage**
Just run this script with python. e.g. `python toranoana_post_process.py`

**Notes**
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent)) # Allow relative import

import re
from typing import Optional, Literal
from bs4 import BeautifulSoup, Tag
from db_wrapper import DBWrapper, DBColumnDescription
from dataclasses import dataclass
from spiders.toranoana_settings import RESOURCES_FOLDER_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_id_and_image_file_name_from_url
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
DB_PATH = RESOURCES_FOLDER_PATH / "toranoana_db.db"
DB_TABLE_NAME = "toranoana_db"

@dataclass
class ToranoanaColumnDescription(DBColumnDescription):
    """Describes database columns."""
    item_id: str
    name: Optional[str] = None
    circles: Optional[str] = None
    creators: Optional[str] = None
    comments: Optional[str] = None
    circle_name: Optional[str] = None
    creator: Optional[str] = None
    genre: Optional[str] = None
    release_date: Optional[str] = None
    type: Optional[str] = None
    
    url: Optional[str] = None
    image_urls: Optional[str] = None # Format is ", ".join(url_list)
    image_file_paths: Optional[str | Literal["ERROR"]] = None # Will be "ERROR" if there is an image url but image file could not be found. Format is ", ".join(path_list)

    @override
    def get_primary_key(self) -> str:
        return "item_id"

class ToranoanaSoupParser:
    """Wraps parsing of Toranoana product page soup."""

    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
        # self.soup_raw = soup.prettify(encoding="utf-8")

        self.item_id, self.url = self._get_item_id_and_url()
        self.name = self._get_name()

        self.circles = self._get_circles()
        self.creators = self._get_creators()
        self.comments = self._get_comments() # json (list)

        table = self._get_table_content()
        self.circle_name = table.get("Circle Name", None)
        self.creator = table.get("Creator", None)
        self.genre = table.get("Genre/Subgenre", None)
        self.release_date = table.get("Publication Date", None)
        self.type = table.get("Type/Size", None)

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
        return str(meta_tag["content"]).strip(" \n")
    
    def _get_circles(self) -> str | None: # <div class="sub-circle">
        a_tags = self.a_tags = self.soup.select('div.sub-circle a')
        if not a_tags:
            return None
        circles = ", ".join([a_tag.get_text() for a_tag in a_tags])

        return circles

    def _get_creators(self) -> str | None: #  <div class="sub-name"> 
        a_tags = self.a_tags = self.soup.select('div.sub-name a')
        if not a_tags:
            return None
        creators = "\n".join([a_tag.get_text() for a_tag in a_tags])

        return creators

    def _get_comments(self) -> str | None:  # Comments
        comment_items = self.soup.select('div.product-detail-comment-item')
        p_tags: list[str] = []
        for comment_item in comment_items:
            p_tag = comment_item.select_one('p')
            if p_tag:
                p_tags.append(p_tag.get_text(strip=True))
        
        return json.dumps(p_tags)
    
    def _get_table_content(self) -> dict[str, str]: # <table class="product-detail-spec-table" data-category="cit"> 
        table = self.soup.select_one('table.product-detail-spec-table[data-category="cit"]')
        if not table:
            return {}
        rows = table.select('tr')
        if not rows:
            return {}
        
        re_cleanup = re.compile(r"[\s]{2,}") # remove multiple spaces/crlf
        out_dict = {}
        for row in rows:
            parsed_row = row.select("td")
            if parsed_row:
                key_tag, value_tag = parsed_row
                txt = value_tag.get_text(strip=True).replace("SetIn-Stock Alert", "")
                out_dict[key_tag.get_text(strip=True)] = re_cleanup.sub(" ", txt)
        
        return out_dict

    def _get_image_urls_and_paths(self) -> tuple[str | None, str | None]: # Retrieve image urls and expected paths. Format is (", ".join(image_urls), ", ".join(image_paths))
        image_urls  = [str(div['data-src']) for div in self.soup.select('div.product-detail-image-thumb-item')]
        if not image_urls :
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
    txt = "===================================================\n Starting Toranoana post processing...\n==================================================="
    print(txt)
    with open(LOG_POSTPROCESSING_PATH, "a+", encoding="utf-8") as f:
        f.write(f'{txt}\n')

    # === Set up database columns ===
    DB_COLUMN_DESCRIPTION = ToranoanaColumnDescription(item_id="TEXT PRIMARY KEY")
    DB_COLUMN_DESCRIPTION.name = "TEXT"
    DB_COLUMN_DESCRIPTION.circles = "TEXT"
    DB_COLUMN_DESCRIPTION.creators = "TEXT"
    DB_COLUMN_DESCRIPTION.comments = "TEXT"
    DB_COLUMN_DESCRIPTION.circle_name = "TEXT"
    DB_COLUMN_DESCRIPTION.creator = "TEXT"
    DB_COLUMN_DESCRIPTION.genre = "TEXT"
    DB_COLUMN_DESCRIPTION.release_date = "TEXT"
    DB_COLUMN_DESCRIPTION.type = "TEXT"
    DB_COLUMN_DESCRIPTION.image_urls = "TEXT"
    # === Database Init ===
    db = DBWrapper(str(DB_PATH), DB_TABLE_NAME, DB_COLUMN_DESCRIPTION)

    # === Process html dumps ===
    for html_file_path in ITEM_HTML_FOLDER_PATH.rglob('*.html'):
        try:
            soup: BeautifulSoup
            # Open file
            with open(html_file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, features="html.parser")
        
            parsed = ToranoanaSoupParser(soup)
            new_item = ToranoanaColumnDescription(
                item_id=parsed.item_id,
                name=parsed.name,
                circles=parsed.circles,
                creators=parsed.creators,
                comments=parsed.comments,
                circle_name=parsed.circle_name,
                creator=parsed.creator,
                genre=parsed.genre,
                release_date=parsed.release_date,
                type=parsed.type,
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