import requests
from urllib import request
import os
import pickle
from lxml import html
import math
import re
import pandas as pd
from time import sleep

PRESS_SEARCH_URL='https://search.metro.tokyo.lg.jp/?ie=u&kw=%E6%96%B0%E5%9E%8B%E3%82%B3%E3%83%AD%E3%83%8A%E3%82%A6%E3%82%A4%E3%83%AB%E3%82%B9%E3%81%AB%E9%96%A2%E9%80%A3%E3%81%97%E3%81%9F%E6%82%A3%E8%80%85%E3%81%AE%E7%99%BA%E7%94%9F%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6&num=10&sitesearch=www.metro.tokyo.lg.jp%2Ftosei%2Fhodohappyo%2Fpress'

RESULT_NUM_XPATH = '//*[@id="search_contents"]/div[1]/span[2]/text()'
URL_PATH='//*[@id="search_contents"]/div[{}]/a/div/div[3]/text()'

OUT_COLUMNS = ['num', 'age', 'travelHistory', 'symptoms', 'sex', 'profession', 'note', 'source']

USE_CACHE = True



def cacheGet(url):
    cache = {}
    if os.path.isfile('cache.pickle'):
        with open('cache.pickle', 'rb') as f:
            cache = pickle.load(f)
    if USE_CACHE and url in cache.keys():
        print('read from chache.')
        return cache[url]
    else:
        print('read from internet.\n sleep 1 sec.')
        sleep(1)
        res = requests.get(url)
        res.encoding = res.apparent_encoding
        cache[url] = res.text
        with open('cache.pickle', 'wb') as f:
            pickle.dump(cache, f)
    return cache[url] 

htmlo = html.fromstring(str(request.urlopen(PRESS_SEARCH_URL).read()))
RESULT_NUM = int(htmlo.xpath(RESULT_NUM_XPATH)[0])
print(RESULT_NUM)


URLS = []
for i in range(RESULT_NUM):
    if i%10 == 0:
        htmlo = html.fromstring(str(request.urlopen(PRESS_SEARCH_URL + '&page={}'.format(1 + i/10)).read()))
    text = htmlo.xpath(URL_PATH.format(i%10 + 2))[0]
    if re.search('http.*html', text) is not None:
        URLS.append(re.search('http.*html', text)[0])


objs = []
for URL in URLS:
    html_string = cacheGet(URL)
    dfs = pd.read_html(html_string)
    for i in range(len(dfs)):
        d = dfs[i]
        if d.get('番号') is None:
            continue
        
        rows = [{'keys': ['番号']}, {'keys': ['年代']}, {'keys': ['渡航歴', '渡航歴【注】']}, {'keys': ['症状']}, {'keys': ['性別']}, {'keys': ['職業']}, {'keys': ['備考', '備　考']}]
        for i in range(len(rows)):
            rows[i]['data'] = pd.DataFrame(['-' for i in range(len(d))])
            for key in rows[i]['keys']:
                data = d.get(key)
                if data is not None:
                    rows[i]['data'] = data
                    break 
        rows.append({'data': pd.DataFrame([URL for i in range(len(d))])})
        ds = pd.concat(map(lambda x: x['data'], rows), axis=1)
        ds.columns = OUT_COLUMNS
        objs.append(ds)


pd.concat(objs).sort_values('num').to_csv('result.csv', index=False)
    



