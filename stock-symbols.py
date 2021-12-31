# Get a list of all stock symbols
import requests
import os
import re 
import time 
import concurrent.futures
import xmltodict
import redis 
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# load me redis
r = redis.Redis(host='localhost', port='6379', db=0)

# input : rows
# output : dict of stocks
def get_data(trs):
    stocks = []
    for tr in trs: 
        tds = tr.find_all("td")
        stock = {
            "name" : tds[0].text, 
            "symbol" : tds[1].text
        }
        stocks.append(stock)

    return stocks

# input : page number
# output : list of array dicts
def get_page(page):
    print(f'Fetching page {page}...')
    url = os.getenv('EDGE_SYMBOLS')
    response = requests.get(url + str(page))
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table", { "class" : "list" })
    tbody = table.find("tbody")
    trs = tbody.find_all("tr")
    stocks = get_data(trs)
    
    return stocks

# input: Takes a symbol string
# output: stock dict
def get_stock_quote(symbol):
    print(f'Getting quote for {symbol}...')
    url = os.getenv('API')
    while(True):
        response = requests.get(url + str(symbol))
        data = xmltodict.parse(response.content)
        d = data["tstock"]["security"]

        stock = {
            "symbol"    : d["@code"], 
            "name"      : d["secname"], 
            "info"      : {
                "date"      : d["stockinfo"]["@logupdate"],
                "last"      : d["stockinfo"]["last"], 
                "open"      : d["stockinfo"]["open"],
                "high"      : d["stockinfo"]["high"], 
                "low"       : d["stockinfo"]["low"],
                "previous"  : d["stockinfo"]["prevclose"],
                "diff"      : d["stockinfo"]["diff"],
                "change"    : d["stockinfo"]["change"],
                "volume"    : d["stockinfo"]["volume"],
                "value"     : d["stockinfo"]["value"], 
                "high-52"   : d["stockinfo"]["wikhi52"],
                "low-52"    : d["stockinfo"]["wiklo52"]
            }
        }

        r.set(stock["symbol"], json.dumps(stock))

        # TODO: Check if this stock changed information in cache
        # if yes:
        #  publish to redis 
        # r.publish(stock["symbol"], json.dumps(stock))
        # r.publish(stock["symbol"], stock["symbol"] + ": last:" + stock["info"]["last"] + " volume: " + stock["info"]["volume"])
        # if no: 
        #  skip

        # sleep
        time.sleep(3)
        # return stock

response = requests.get(os.getenv('EDGE_SYMBOLS'))
soup = BeautifulSoup(response.text, 'html.parser')
count = soup.find("span", { "class" : "count"})

max_pages = re.search(r"\D[0-9]\D*([0-9]+)\D*[0-9]+\D", count.text)
pages = int(max_pages.group(1))

stocks = []

# Concurrently get all stock symbol from PSE and save to stocks array
with concurrent.futures.ThreadPoolExecutor() as executor: 
    list_of_pages = [page + 1 for page in range(pages)]

    # submit method get_page with params page to the pool
    results = [executor.submit(get_page, page) for page in list_of_pages]

    # as it completes, insert into stocks list
    for f in concurrent.futures.as_completed(results):
        stocks.extend(f.result())

# testing purposes
# stocks = [
#     { "symbol" : "MONDE" }, 
#     { "symbol" : "CNVRG" }, 
#     { "symbol" : "SCC" }, 
#     { "symbol" : "MBT" },
#     { "symbol" : "URC" }
# ]


# Get quotes of each one
workers = len(stocks) + 10
with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor: 
    results = [executor.submit(get_stock_quote, stock["symbol"]) for stock in stocks]


