# =========================================================================
# Change surugaya html dumps to use css local styles and images, or restore the files
# =========================================================================

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent)) # Allow relative import

import re
from typing import Optional, Literal
from bs4 import BeautifulSoup
from db_wrapper import DBWrapper, DBColumnDescription
from dataclasses import dataclass
from spiders.surugaya_settings import LOG_IMAGES_PATH, ITEM_HTML_FOLDER_PATH, ITEM_IMAGE_FOLDER_PATH, get_id_and_image_file_name_from_url, RESOURCES_FOLDER_PATH
try:
    from typing import override
except ImportError:
    def override(func): # dummy decorator for compatibility with Python < 3.12
        return func
    
PATH_LOCAL_CSS = Path(__file__).parent / "assets" / "surugaya"

def get_image_url(soup) -> str | None: # Retrieve info from <script type="application/ld+json">
    script_application_tag = soup.find('script', string=lambda text: text and 'releaseDate' in text)
    if not script_application_tag:
        return None
    script_content = script_application_tag.string
    re_image_url = re.compile(r'"(image)"\s?:\s?"([^"]*)",')
    iu = re_image_url.search(script_content)
    return iu.group(2) if iu else None

print(f"=== {__file__} ===")
print("-> Change the surugaya html files to use local css files. This should be non destructive.")
ask = input("# Action:\n 'enable'/'e': enable local css files\n 'disable'/'d': restore html files to original form.\n")
if ask in ("enable", "e"):
    for file in ITEM_HTML_FOLDER_PATH.glob("*.html"):
        with file.open("r", encoding='utf-8') as f:
            content = f.read()

        # == Replace css urls ==
        content = re.sub(r'"[^"]*css_YLUY2usEybPXqNO15-ozAgAYsZmniqhrU6f3bp69-r4.css', '"' + str((PATH_LOCAL_CSS / "styles1.css").relative_to(ITEM_HTML_FOLDER_PATH, walk_up=True)).replace("\\","/"), content)
        content = re.sub(r'"[^"]*css_LmUrbIckCDCKvN2_Q3zbp044aJ28BPsL4EcroazBk2w.css', '"' + str((PATH_LOCAL_CSS / "styles2.css").relative_to(ITEM_HTML_FOLDER_PATH, walk_up=True)).replace("\\","/"), content)
        content = re.sub(r'"[^"]*new_pc_product_detail.css', '"' + str((PATH_LOCAL_CSS / "new_pc_product_detail.css").relative_to(ITEM_HTML_FOLDER_PATH, walk_up=True)).replace("\\","/"), content)

        # == Replace image paths ==
        soup = BeautifulSoup(content, features="html.parser")
        image_url = get_image_url(soup)
        if image_url:
            local_path = (ITEM_IMAGE_FOLDER_PATH / get_id_and_image_file_name_from_url(image_url)[1]).relative_to(ITEM_HTML_FOLDER_PATH,walk_up=True)
            content = content.replace(image_url, str(local_path).replace('\\', "/"))
            content = content.replace(f'"image": "{str(local_path).replace("\\","/")}"', f'"image": "{image_url}"')

        with file.open("w", encoding='utf-8') as f:
            f.write(content)
        print(f"Updated '{file}'")

elif ask in ("disable", "d"):
    for file in ITEM_HTML_FOLDER_PATH.glob("*.html"):
        with file.open("r", encoding='utf-8') as f:
            content = f.read()
        # Replace css urls
        content = re.sub(r'"[^"]*styles1.css', '"/drupal/sites/default/files/css/css_YLUY2usEybPXqNO15-ozAgAYsZmniqhrU6f3bp69-r4.css', content)
        content = re.sub(r'"[^"]*styles2.css', '"/drupal/sites/default/files/css/css_LmUrbIckCDCKvN2_Q3zbp044aJ28BPsL4EcroazBk2w.css', content)
        content = re.sub(r'"[^"]*new_pc_product_detail.css', '"/drupal/modules/product_detail/assets/css/new_pc_product_detail.css', content)

        # == Replace image paths ==
        soup = BeautifulSoup(content, features="html.parser")
        image_url = get_image_url(soup)
        if image_url:
            local_path = (ITEM_IMAGE_FOLDER_PATH / get_id_and_image_file_name_from_url(image_url)[1]).relative_to(ITEM_HTML_FOLDER_PATH,walk_up=True)
            content = content.replace(str(local_path).replace('\\', "/"), image_url)

        with file.open("w", encoding='utf-8') as f:
            f.write(content)
        print(f"Restored '{file}'")
else:
    print("Aborted !")
    exit()