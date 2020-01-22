from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
import json
import time

db = client.SSLT2019WINTER
app = SnuScraper('2019', '겨울학기', 'U000200002U000300002', 25, db)

# init_scraper(app, 5)
app.update_db()