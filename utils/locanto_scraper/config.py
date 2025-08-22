"""'
Lists constants and mappings used in the parent folder - web_scraping
"""

from utils.locanto_scraper.scraper_helper_functions import (
    find_by_id,
    find_by_class,
    find_by_itemprop,
    find_tag_only,
    extract_feature_list,
)

WEBSITE_TO_SCRAPE = "https://www.locanto.com.au/"
DEFAULT_JOB_TO_SEARCH = "Data Scientist"
DEFAULT_LOCATION = "Melbourne"
ITEMS_TO_SCRAPE = [
    "id",
    "Job position",
    "Company name",
    "description",
    "suburb",
    "posted_date",
    "salary",
]
ITEM_HTML_TAG_MAPPING = {
    "id": "a",
    "Job position": "li",
    "Company name": "li",
    "description": "div",
    "suburb": "span",
    "posted_date": "div",
    "salary": "div",
}

ID_VALUE_LIST = ["id"]
CLASS_VALUE_LIST = [
    "Job position",
    "Company name",
    "description",
    "posted_date",
    "salary",
]
ITEMPROP_LIST = ["suburb"]
ITEM_HTML_ATTRIBUTE_MAPPING = {
    "id": "adID",
    "Job position": "vap_user_content__feature_element",
    "description": "vap__description",
    "suburb": "addressLocality",
    "salary": "vap_user_content__price",
    "Company name": "vap_user_content__feature_element",
}
SEARCH_STRATEGIES = {
    "id": find_by_id,
    "class": find_by_class,
    "itemprop": find_by_itemprop,
    "tag_only": find_tag_only,
    "list": extract_feature_list,
}
ITEM_SEARCH_STRATEGY = {
    "id": "id",
    "Job position": "list",
    "description": "class",
    "suburb": "itemprop",
    "posted_date": "class",
    "salary": "class",
    "Company name": "list",
}
