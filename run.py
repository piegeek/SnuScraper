from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
import sys

db = client.SSLT2019WINTER
app = SnuScraper('2019', '겨울학기', 'U000200002U000300002', 25, db)

try:
    if sys.argv[1] == '--init':
        init_scraper(app, 5)
except IndexError:
    pass

app.run()