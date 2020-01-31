from SnuScraper import client
from SnuScraper.scraper import SnuScraper, init_scraper
from os.path import join
import json
import time
import threading

db = client.SSLT2019WINTER
app = SnuScraper('2019', '겨울학기', 'U000200002U000300002', 25, db, debug=False)

# init_scraper(app, 0.1)
# app.run()

start = time.time()

# data = []

# Synchronous code
# for i in range(1,9):
#     results = app.get_page_student_data(i)
#     for result in results:
#         data.append(result)

# Asynchronous code
# threads = []

# def save_to_data(scraper_app, data_list, page_num):
#     results = scraper_app.get_page_student_data(page_num)
#     for result in results:
#         data_list.append(result)

# for i in range(1,9):
#     thread = threading.Thread(target=save_to_data, args=(app, data, i))
#     threads.append(thread)
#     thread.start()

# for thread in threads:
#     thread.join()

# print(data)

print(app.get_student_data())

finish = time.time()

print(f'Total duration: {finish - start} seconds.')