from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
import sys

db = client.SSLT2020SPRING
app = SnuScraper('2020', '1학기', 'U000200001U000300001', 794, db, debug=True)

try:
    if sys.argv[1] == '--init':
        init_scraper(app, 5)
except IndexError:
    pass

app.run()