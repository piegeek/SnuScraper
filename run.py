from SnuScraper.scraper import SnuScraper, init_scraper
import json

app = SnuScraper()

my_df = app.load_spread_sheet('2019-WINTER.xls')

app.save_df_to_db(my_df)