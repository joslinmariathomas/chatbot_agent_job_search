from bs4 import BeautifulSoup, Tag


# Functions to find html tags and values from a html url
def find_by_id(soup: BeautifulSoup, tag: str, value: str | None):
    return soup.find(name=tag, id=value)


def find_by_class(soup: BeautifulSoup, tag: str, value: str | None):
    if value == "vap_user_content__date_label":
        span = soup.find(name=tag, class_=value)
        return span.next_sibling
    return soup.find(name=tag, class_=value)


def find_by_itemprop(soup: BeautifulSoup, tag: str, value: str | None):
    return soup.find(name=tag, itemprop=value)


def find_tag_only(soup: BeautifulSoup, tag: str, value: str | None = None):
    return soup.find(name=tag)


def extract_feature_list(soup: BeautifulSoup, feature_name: str, tag: str, value: str):
    for i in range(5):
        for li in soup.find_all(name=tag, class_=value):
            name = li.find(name="div", class_="vap_user_content__feature_name")
            value_of_feature = li.find(
                name="div", class_="vap_user_content__feature_value"
            )
            if name is not None and value is not None:
                if name.text.strip() == feature_name:
                    return value_of_feature.text.strip()
            else:
                value = f"{value} "
    return None


def cleanup_html_tag(item: str, html_retrieved_value: Tag) -> str:
    """Cleans and formats extracted HTML content based on item type."""
    if not html_retrieved_value:
        return ""
    if item == "price" and html_retrieved_value:
        html_retrieved_value = html_retrieved_value.find("div")
    if item == "posted_date":
        if html_retrieved_value:
            return html_retrieved_value
        else:
            return "no_date"
    html_retrieved_value = (
        html_retrieved_value.get_text(strip=True) if html_retrieved_value else ""
    )
    return html_retrieved_value
