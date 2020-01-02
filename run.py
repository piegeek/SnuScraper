from SnuScraper.scraper import SnuScraper, init_scraper
import json
import time

app = SnuScraper('2020', '1학기', 'U000200001U000300001', 790)
old_app = SnuScraper('2017', '1학기', 'U000200001U000300001', 25)

init_scraper(app)