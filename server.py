import sys
import json
import requests
from bs4 import BeautifulSoup
import re

def fetch_item_data(appid, item_name):
    """Fetch Steam market item data including current price and price history"""
    base_url = f"https://steamcommunity.com/market/listings/{appid}/{item_name.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"error": f"Steam market response failed with status {response.status_code}"}

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
            except Exception as e:
                last_10_days_prices = []

        return {
            "item_name": item_name,
            "appid": appid,
            "current_price": current_price,
            "last_10_days_prices": last_10_days_prices,
            "market_url": base_url
        }
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

def main():
    """Main MCP server loop"""
    try:
        for line in sys.stdin:
            try:
                req = json.loads(line.strip())
                id_ = req.get("id")
                method = req.get("method")

                if method == "initialize":
                    resp = {
                        "jsonrpc": "2.0",
                        "id": id_,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "steamtools-mcp",
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    resp = {
                        "jsonrpc": "2.0",
                        "id": id_,
                        "result": {
                            "tools": [
                                {
                                    "name": "get_steam_item_data",
                                    "description": "Fetch Steam market item data including current price and price history for the last 10 days",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "appid": {
                                                "type": "string",
                                                "description": "Steam application ID (e.g., '730' for CS:GO, '440' for TF2)"
                                            },
                                            "item_name": {
                                                "type": "string",
                                                "description": "Name of the item to search for in the Steam market"
                                            }
                                        },
                                        "required": ["appid", "item_name"]
                                    }
                                }
                            ]
                        }
                    }
                elif method == "tools/call":
                    params = req.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})

                    if tool_name == "get_steam_item_data":
                        appid = arguments.get("appid")
                        item_name = arguments.get("item_name")

                        if not appid or not item_name:
                            resp = {
                                "jsonrpc": "2.0",
                                "id": id_,
                                "error": {
                                    "code": -32602,
                                    "message": "Invalid params: appid and item_name are required"
                                }
                            }
                        else:
                            result = fetch_item_data(appid, item_name)
                            resp = {
                                "jsonrpc": "2.0",
                                "id": id_,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": json.dumps(result, indent=2)
                                        }
                                    ]
                                }
                            }
                    else:
                        resp = {
                            "jsonrpc": "2.0",
                            "id": id_,
                            "error": {
                                "code": -32601,
                                "message": f"Tool not found: {tool_name}"
                            }
                        }
                else:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": id_,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }

                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            except json.JSONDecodeError as e:
                error_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                sys.stdout.write(json.dumps(error_resp) + "\n")
                sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        error_resp = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
        sys.stdout.write(json.dumps(error_resp) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()