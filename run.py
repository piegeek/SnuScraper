from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
import json
import time

db = client.SSLT2020SPRING

app = SnuScraper('2020', '1학기', 'U000200001U000300001', 790, db)

init_scraper(app)