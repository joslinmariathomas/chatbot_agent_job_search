import datetime as dt
from dataclasses import dataclass

import cloudscraper
from bs4 import BeautifulSoup
from typing import Optional

from utils.locanto_scraper.config import (
    WEBSITE_TO_SCRAPE,
    DEFAULT_JOB_TO_SEARCH,
    DEFAULT_LOCATION,
    ITEMS_TO_SCRAPE,
    ITEM_HTML_TAG_MAPPING,
    ITEM_HTML_ATTRIBUTE_MAPPING,
    ITEM_SEARCH_STRATEGY,
    SEARCH_STRATEGIES,
)
from utils.locanto_scraper.scraper_helper_functions import cleanup_html_tag


@dataclass
class Joblisting:
    id: str
    title: str
    company: str
    suburb: str
    description: str
    posted_date: str
    salary: Optional[str]
    url: str


class LocantoScraper:
    def __init__(
        self,
        job_to_search: str,
        location: str,
    ):
        self.base_url = WEBSITE_TO_SCRAPE
        self.job_to_search = job_to_search.replace(" ", "+")
        self.location = location
        self.url = f"{self.base_url}{self.location}/q/?query={self.job_to_search}"
        self.no_of_pages_to_scrape = 1
        self.job_listings = []

    def scrape(self):
        for page_index in range(self.no_of_pages_to_scrape):
            url = f"{self.url}&page={page_index}"
            self.get_ads_from_a_single_page(url=url)

    @staticmethod
    def get_soup(url: str) -> BeautifulSoup:
        scraper = cloudscraper.create_scraper()
        res = scraper.get(url, timeout=60)
        return BeautifulSoup(res.content, "html.parser")

    def get_ads_from_a_single_page(self, url: str):
        """Collects ad details from all listings on a single search result page."""
        soup = self.get_soup(url=url)
        ad_html_list = self.get_individual_ads_html(soup=soup)
        for ad_html in ad_html_list:
            ad_detail_dict = self.parse_ad_detail(ad_html)
            self.job_listings.append(ad_detail_dict)

    @staticmethod
    def get_individual_ads_html(soup: BeautifulSoup) -> list[str]:
        """Extracts individual ad URLs from the soup object."""
        ads_list = list(soup.select("a[href*='ID_']"))
        ads_html_list = [link["href"] for link in ads_list]
        return ads_html_list

    def parse_ad_detail(self, url: str) -> dict:
        """Scrapes and parses the details of a single ad page."""
        print(f"[+] Scraping: {url}")
        soup = self.get_soup(url)
        html_dict = {}
        for item in ITEMS_TO_SCRAPE:
            tag = ITEM_HTML_TAG_MAPPING.get(item)
            attr_value = ITEM_HTML_ATTRIBUTE_MAPPING.get(item)
            strategy = ITEM_SEARCH_STRATEGY.get(item, "tag_only")
            html_tag_finder = SEARCH_STRATEGIES[strategy]
            try:
                if strategy == "list":
                    cleaned_retrieved_value = html_tag_finder(
                        feature_name=item, soup=soup, tag=tag, value=attr_value
                    )
                    html_dict[item] = cleaned_retrieved_value
                else:
                    html_retrieved_value = html_tag_finder(
                        soup=soup, tag=tag, value=attr_value
                    )
                    cleaned = cleanup_html_tag(
                        html_retrieved_value=html_retrieved_value, item=item
                    )
                    html_dict[item] = cleaned
            except Exception as e:
                print(f"[Not OK] {item}")
        if html_dict:
            html_dict["extraction_date"] = dt.datetime.now().astimezone().date()
        return html_dict

