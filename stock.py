# Stock info for each stock
import requests
import xmltodict
import json
import os
from dotenv import load_dotenv

load_dotenv()

response = requests.get(os.getenv('API'))
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

print(stock)

