from utils.locanto_scraper.locanto_scraper import LocantoScraper


def test_locanto_scraper():

    job = "Data Scientist"
    location = "Sydney"
    scraper = LocantoScraper(
        job_to_search=job,
        location=location,
    )
    scraper.scrape()
    job_listings = scraper.job_listings
    assert len(job_listings) > 10
    assert type(job_listings[0]) == dict
