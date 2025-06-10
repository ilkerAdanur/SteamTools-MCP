from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
import json

app = FastAPI()

class ItemRequest(BaseModel):
    appid: str
    item_name: str

@app.post("/get_item_data")
def get_item_data(req: ItemRequest):
    base_url = f"https://steamcommunity.com/market/listings/{req.appid}/{req.item_name.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        return {"error": "Steam market response failed"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Current price
    price_span = soup.find("span", class_="market_listing_price market_listing_price_with_fee")
    current_price = price_span.text.strip() if price_span else "N/A"

    # Get price history (JavaScript embedded data)
    match = re.search(r"var line1=(\[.*?\]);", response.text)
    last_10_days_prices = []
    if match:
        try:
            data = json.loads(match.group(1))
            for entry in data[-10:]:
                last_10_days_prices.append({
                    "date": entry[0],
                    "price": entry[1],
                    "sales": entry[2]
                })
        except:
            last_10_days_prices = []

    return {
        "item_name": req.item_name,
        "appid": req.appid,
        "current_price": current_price,
        "last_10_days_prices": last_10_days_prices
    }

def main():
    for line in sys.stdin:
        req = json.loads(line)
        id_ = req.get("id")
        m = req.get("method")

        if m == "initialize":
            resp = {"jsonrpc":"2.0","id":id_,"result":{"name":"steamtools-mcp","capabilities":{"tools":{"listChanged":False}}}}
        elif m == "tools/list":
            resp = {"jsonrpc":"2.0","id":id_,"result":{"tools":[{"name":"get_item_data","description":"Fetch current and last-10-days prices","inputSchema":{"type":"object","properties":{"appid":{"type":"string"},"item_name":{"type":"string"}},"required":["appid","item_name"]}}]}}
        elif m == "tools/call":
            params = req["params"]
            if params["name"]=="get_item_data":
                result = fetch_item_data(params["arguments"]["appid"], params["arguments"]["item_name"])
                resp = {"jsonrpc":"2.0","id":id_,"result":result}
            else:
                resp = {"jsonrpc":"2.0","id":id_,"error":{"code":-32601,"message":"Tool not found"}}
        else:
            resp = {"jsonrpc":"2.0","id":id_,"error":{"code":-32601,"message":"Method not found"}}

        sys.stdout.write(json.dumps(resp)+"\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()