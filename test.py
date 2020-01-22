from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
from os.path import join
import json
import time

db = client.SSLT2019WINTER
app = SnuScraper('2019', '겨울학기', 'U000200002U000300002', 25, db, debug=True)

# init_scraper(app, 0.1)
# app.run()

# print(app.load_spread_sheet('2019-겨울학기-debug.xls').tail())

app.update_df_to_db(app.load_spread_sheet('2019-겨울학기-debug.xls'))

# init_scraper(app, 0.1)
# app.run()

# print(app.get_page_student_data(4))

# db = client.SSLT2020SPRING
# app = SnuScraper('2020', '1학기', 'U000200001U000300001', 792, db, debug=True)

# init_scraper(app, 0.2)
# app.run()