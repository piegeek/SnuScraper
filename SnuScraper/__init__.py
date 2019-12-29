import json

SITE_URL = "http://sugang.snu.ac.kr/sugang/cc/cc100excel.action"

with open('Params.txt', 'r+', encoding='utf-8') as input_file:
    PARAMS = json.loads(input_file.read())