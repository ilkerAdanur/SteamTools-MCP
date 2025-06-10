import sys
import json
import requests
from bs4 import BeautifulSoup
import re

def fetch_item_data(appid, item_name):
    """Fetch Steam market item data including current price and price history"""
    # URL encode the item name properly
    import urllib.parse
    encoded_item_name = urllib.parse.quote(item_name)
    base_url = f"https://steamcommunity.com/market/listings/{appid}/{encoded_item_name}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        # Add session for better request handling
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(base_url, timeout=15)
        if response.status_code != 200:
            return {
                "error": f"Steam market response failed with status {response.status_code}",
                "item_name": item_name,
                "appid": appid,
                "market_url": base_url
            }

        soup = BeautifulSoup(response.text, "html.parser")

        # Check if item exists
        error_msg = soup.find("div", {"id": "message"})
        if error_msg and "no longer available" in error_msg.get_text().lower():
            return {
                "error": "Item not found or no longer available in the market",
                "item_name": item_name,
                "appid": appid,
                "market_url": base_url
            }

        # Current price - try multiple selectors
        current_price = "N/A"
        price_selectors = [
            "span.market_listing_price.market_listing_price_with_fee",
            "span.market_listing_price_with_fee",
            "span.market_listing_price",
            ".market_listing_price_with_fee",
            ".market_listing_price"
        ]

        for selector in price_selectors:
            price_span = soup.select_one(selector)
            if price_span and price_span.text.strip():
                current_price = price_span.text.strip()
                break

        # Get price history from multiple possible sources
        last_10_days_prices = []

        # Try to find price history data in JavaScript
        js_patterns = [
            r"var line1=(\[.*?\]);",
            r"line1=(\[.*?\]);",
            r'"line1":(\[.*?\])',
            r"g_rgAssetPriceHistory\s*=\s*(\[.*?\]);"
        ]

        for pattern in js_patterns:
            match = re.search(pattern, response.text)
            if match:
                try:
                    data = json.loads(match.group(1))
                    for entry in data[-10:]:
                        if len(entry) >= 3:
                            last_10_days_prices.append({
                                "date": entry[0],
                                "price": entry[1],
                                "sales": entry[2]
                            })
                    break
                except Exception:
                    continue

        # Get item description and exterior
        item_description = ""
        exterior = ""

        # Try to extract exterior from item name or page
        exterior_match = re.search(r'\((.*?)\)$', item_name)
        if exterior_match:
            exterior = exterior_match.group(1)

        # Look for item description
        desc_elem = soup.find("div", class_="market_listing_item_name_block")
        if desc_elem:
            item_description = desc_elem.get_text(strip=True)

        return {
            "item_name": item_name,
            "appid": appid,
            "current_price": current_price,
            "exterior": exterior,
            "description": item_description,
            "last_10_days_prices": last_10_days_prices,
            "market_url": base_url,
            "data_points": len(last_10_days_prices),
            "status": "success" if current_price != "N/A" else "partial_data"
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout - Steam servers may be slow",
            "item_name": item_name,
            "appid": appid,
            "market_url": base_url
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Network error: {str(e)}",
            "item_name": item_name,
            "appid": appid,
            "market_url": base_url
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch data: {str(e)}",
            "item_name": item_name,
            "appid": appid,
            "market_url": base_url
        }

def search_steam_items(appid, search_term, max_results=10):
    """Search for items in Steam market by name"""
    import urllib.parse

    search_url = f"https://steamcommunity.com/market/search/render/"
    params = {
        'query': search_term,
        'start': 0,
        'count': max_results,
        'search_descriptions': 0,
        'sort_column': 'popular',
        'sort_dir': 'desc',
        'appid': appid,
        'norender': 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://steamcommunity.com/market/search?appid={appid}"
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(search_url, params=params, timeout=15)
        if response.status_code != 200:
            return {
                "error": f"Search failed with status {response.status_code}",
                "search_term": search_term,
                "appid": appid
            }

        data = response.json()

        if not data.get('success'):
            return {
                "error": "Search request was not successful",
                "search_term": search_term,
                "appid": appid
            }

        results = []
        if 'results_html' in data and data['results_html']:
            soup = BeautifulSoup(data['results_html'], 'html.parser')
            items = soup.find_all('a', class_='market_listing_row_link')

            for item in items[:max_results]:
                try:
                    # Extract item name
                    name_elem = item.find('span', class_='market_listing_item_name')
                    item_name = name_elem.text.strip() if name_elem else "Unknown"

                    # Extract price
                    price_elem = item.find('span', class_='normal_price')
                    if not price_elem:
                        price_elem = item.find('span', class_='sale_price')
                    price = price_elem.text.strip() if price_elem else "N/A"

                    # Extract item URL
                    item_url = item.get('href', '')

                    # Extract quantity if available
                    qty_elem = item.find('span', class_='market_listing_num_listings_qty')
                    quantity = qty_elem.text.strip() if qty_elem else "N/A"

                    results.append({
                        "name": item_name,
                        "price": price,
                        "quantity_available": quantity,
                        "market_url": item_url
                    })
                except Exception as e:
                    continue

        return {
            "search_term": search_term,
            "appid": appid,
            "total_results": data.get('total_count', 0),
            "results": results,
            "status": "success"
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Search timeout - Steam servers may be slow",
            "search_term": search_term,
            "appid": appid
        }
    except Exception as e:
        return {
            "error": f"Search failed: {str(e)}",
            "search_term": search_term,
            "appid": appid
        }

def get_popular_items_24h(appid, max_results=10):
    """Get most popular items in the last 24 hours by sales volume"""
    popular_url = f"https://steamcommunity.com/market/popular/render/"
    params = {
        'start': 0,
        'count': max_results,
        'country': 'US',
        'language': 'english',
        'currency': 1,
        'appid': appid,
        'norender': 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://steamcommunity.com/market/popular?appid={appid}"
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(popular_url, params=params, timeout=15)
        if response.status_code != 200:
            return {
                "error": f"Popular items request failed with status {response.status_code}",
                "appid": appid
            }

        data = response.json()

        if not data.get('success'):
            return {
                "error": "Popular items request was not successful",
                "appid": appid
            }

        results = []
        if 'results_html' in data and data['results_html']:
            soup = BeautifulSoup(data['results_html'], 'html.parser')
            items = soup.find_all('a', class_='market_listing_row_link')

            for item in items[:max_results]:
                try:
                    # Extract item name
                    name_elem = item.find('span', class_='market_listing_item_name')
                    item_name = name_elem.text.strip() if name_elem else "Unknown"

                    # Extract current price
                    price_elem = item.find('span', class_='normal_price')
                    if not price_elem:
                        price_elem = item.find('span', class_='sale_price')
                    current_price = price_elem.text.strip() if price_elem else "N/A"

                    # Extract quantity sold (24h sales)
                    qty_elem = item.find('span', class_='market_listing_num_listings_qty')
                    sales_24h = qty_elem.text.strip() if qty_elem else "N/A"

                    # Extract item URL
                    item_url = item.get('href', '')

                    # Try to get additional data from the item page
                    item_data = {
                        "name": item_name,
                        "current_price": current_price,
                        "sales_24h": sales_24h,
                        "market_url": item_url
                    }

                    # Try to extract more detailed info if available
                    game_elem = item.find('span', class_='market_listing_game_name')
                    if game_elem:
                        item_data["game"] = game_elem.text.strip()

                    results.append(item_data)

                except Exception as e:
                    continue

        return {
            "appid": appid,
            "period": "24_hours",
            "type": "most_popular",
            "results": results,
            "total_found": len(results),
            "status": "success"
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout - Steam servers may be slow",
            "appid": appid
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch popular items: {str(e)}",
            "appid": appid
        }

def get_most_expensive_sold_24h(appid, max_results=10):
    """Get most expensive items sold in the last 24 hours"""
    # Steam doesn't have a direct API for this, so we'll use recent activity
    recent_url = f"https://steamcommunity.com/market/recent/render/"
    params = {
        'start': 0,
        'count': 100,  # Get more to find expensive ones
        'country': 'US',
        'language': 'english',
        'currency': 1,
        'appid': appid,
        'norender': 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://steamcommunity.com/market/recent?appid={appid}"
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(recent_url, params=params, timeout=15)
        if response.status_code != 200:
            return {
                "error": f"Recent sales request failed with status {response.status_code}",
                "appid": appid
            }

        data = response.json()

        if not data.get('success'):
            return {
                "error": "Recent sales request was not successful",
                "appid": appid
            }

        results = []
        if 'results_html' in data and data['results_html']:
            soup = BeautifulSoup(data['results_html'], 'html.parser')
            items = soup.find_all('a', class_='market_recent_listing_row')

            price_items = []
            for item in items:
                try:
                    # Extract item name
                    name_elem = item.find('span', class_='market_listing_item_name')
                    item_name = name_elem.text.strip() if name_elem else "Unknown"

                    # Extract sale price
                    price_elem = item.find('span', class_='market_table_value')
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # Extract numeric value for sorting
                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                        if price_match:
                            price_value = float(price_match.group().replace(',', ''))

                            # Extract sale time
                            time_elem = item.find('span', class_='market_listing_listed_date')
                            sale_time = time_elem.text.strip() if time_elem else "Unknown"

                            price_items.append({
                                "name": item_name,
                                "sale_price": price_text,
                                "sale_price_value": price_value,
                                "sale_time": sale_time,
                                "market_url": item.get('href', '')
                            })

                except Exception as e:
                    continue

            # Sort by price (highest first) and take top results
            price_items.sort(key=lambda x: x['sale_price_value'], reverse=True)
            results = price_items[:max_results]

            # Remove the numeric value used for sorting
            for item in results:
                del item['sale_price_value']

        return {
            "appid": appid,
            "period": "24_hours",
            "type": "most_expensive_sold",
            "results": results,
            "total_found": len(results),
            "status": "success"
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout - Steam servers may be slow",
            "appid": appid
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch expensive sold items: {str(e)}",
            "appid": appid
        }

def get_most_expensive_sold_weekly(appid, max_results=10):
    """Get most expensive items sold in the last week"""
    # Use search with high price sorting
    search_url = f"https://steamcommunity.com/market/search/render/"
    params = {
        'query': '',
        'start': 0,
        'count': max_results,
        'search_descriptions': 0,
        'sort_column': 'price',
        'sort_dir': 'desc',
        'appid': appid,
        'norender': 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://steamcommunity.com/market/search?appid={appid}"
    }

    try:
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(search_url, params=params, timeout=15)
        if response.status_code != 200:
            return {
                "error": f"Weekly expensive items request failed with status {response.status_code}",
                "appid": appid
            }

        data = response.json()

        if not data.get('success'):
            return {
                "error": "Weekly expensive items request was not successful",
                "appid": appid
            }

        results = []
        if 'results_html' in data and data['results_html']:
            soup = BeautifulSoup(data['results_html'], 'html.parser')
            items = soup.find_all('a', class_='market_listing_row_link')

            for item in items[:max_results]:
                try:
                    # Extract item name
                    name_elem = item.find('span', class_='market_listing_item_name')
                    item_name = name_elem.text.strip() if name_elem else "Unknown"

                    # Extract current price
                    price_elem = item.find('span', class_='normal_price')
                    if not price_elem:
                        price_elem = item.find('span', class_='sale_price')
                    current_price = price_elem.text.strip() if price_elem else "N/A"

                    # Extract quantity available
                    qty_elem = item.find('span', class_='market_listing_num_listings_qty')
                    quantity = qty_elem.text.strip() if qty_elem else "N/A"

                    # Extract item URL
                    item_url = item.get('href', '')

                    results.append({
                        "name": item_name,
                        "current_price": current_price,
                        "quantity_available": quantity,
                        "market_url": item_url
                    })

                except Exception as e:
                    continue

        return {
            "appid": appid,
            "period": "weekly",
            "type": "most_expensive_available",
            "results": results,
            "total_found": len(results),
            "status": "success"
        }

    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout - Steam servers may be slow",
            "appid": appid
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch weekly expensive items: {str(e)}",
            "appid": appid
        }

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
                                    "description": "Fetch detailed Steam market data for a specific item including current price and price history",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "appid": {
                                                "type": "string",
                                                "description": "Steam application ID (e.g., '730' for CS:GO, '440' for TF2)"
                                            },
                                            "item_name": {
                                                "type": "string",
                                                "description": "Exact name of the item including exterior condition (e.g., 'AK-47 | Redline (Field-Tested)')"
                                            }
                                        },
                                        "required": ["appid", "item_name"]
                                    }
                                },
                                {
                                    "name": "search_steam_items",
                                    "description": "Search for items in Steam market by name and get a list of matching items with prices",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "appid": {
                                                "type": "string",
                                                "description": "Steam application ID (e.g., '730' for CS:GO, '440' for TF2)"
                                            },
                                            "search_term": {
                                                "type": "string",
                                                "description": "Search term to find items (e.g., 'AK-47 Redline' to find all Redline variants)"
                                            },
                                            "max_results": {
                                                "type": "integer",
                                                "description": "Maximum number of results to return (default: 10, max: 50)",
                                                "default": 10,
                                                "minimum": 1,
                                                "maximum": 50
                                            }
                                        },
                                        "required": ["appid", "search_term"]
                                    }
                                },
                                {
                                    "name": "get_popular_items_24h",
                                    "description": "Get most popular items in the last 24 hours by sales volume with current prices and sales data",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "appid": {
                                                "type": "string",
                                                "description": "Steam application ID (e.g., '730' for CS:GO, '440' for TF2)"
                                            },
                                            "max_results": {
                                                "type": "integer",
                                                "description": "Maximum number of results to return (default: 10, max: 20)",
                                                "default": 10,
                                                "minimum": 1,
                                                "maximum": 20
                                            }
                                        },
                                        "required": ["appid"]
                                    }
                                },
                                {
                                    "name": "get_most_expensive_sold_24h",
                                    "description": "Get most expensive items sold in the last 24 hours with sale prices and times",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "appid": {
                                                "type": "string",
                                                "description": "Steam application ID (e.g., '730' for CS:GO, '440' for TF2)"
                                            },
                                            "max_results": {
                                                "type": "integer",
                                                "description": "Maximum number of results to return (default: 10, max: 20)",
                                                "default": 10,
                                                "minimum": 1,
                                                "maximum": 20
                                            }
                                        },
                                        "required": ["appid"]
                                    }
                                },
                                {
                                    "name": "get_most_expensive_sold_weekly",
                                    "description": "Get most expensive items available for sale (weekly high-value items) with current prices",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "appid": {
                                                "type": "string",
                                                "description": "Steam application ID (e.g., '730' for CS:GO, '440' for TF2)"
                                            },
                                            "max_results": {
                                                "type": "integer",
                                                "description": "Maximum number of results to return (default: 10, max: 20)",
                                                "default": 10,
                                                "minimum": 1,
                                                "maximum": 20
                                            }
                                        },
                                        "required": ["appid"]
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

                    elif tool_name == "search_steam_items":
                        appid = arguments.get("appid")
                        search_term = arguments.get("search_term")
                        max_results = arguments.get("max_results", 10)

                        if not appid or not search_term:
                            resp = {
                                "jsonrpc": "2.0",
                                "id": id_,
                                "error": {
                                    "code": -32602,
                                    "message": "Invalid params: appid and search_term are required"
                                }
                            }
                        else:
                            # Validate max_results
                            if not isinstance(max_results, int) or max_results < 1 or max_results > 50:
                                max_results = 10

                            result = search_steam_items(appid, search_term, max_results)
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

                    elif tool_name == "get_popular_items_24h":
                        appid = arguments.get("appid")
                        max_results = arguments.get("max_results", 10)

                        if not appid:
                            resp = {
                                "jsonrpc": "2.0",
                                "id": id_,
                                "error": {
                                    "code": -32602,
                                    "message": "Invalid params: appid is required"
                                }
                            }
                        else:
                            # Validate max_results
                            if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
                                max_results = 10

                            result = get_popular_items_24h(appid, max_results)
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

                    elif tool_name == "get_most_expensive_sold_24h":
                        appid = arguments.get("appid")
                        max_results = arguments.get("max_results", 10)

                        if not appid:
                            resp = {
                                "jsonrpc": "2.0",
                                "id": id_,
                                "error": {
                                    "code": -32602,
                                    "message": "Invalid params: appid is required"
                                }
                            }
                        else:
                            # Validate max_results
                            if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
                                max_results = 10

                            result = get_most_expensive_sold_24h(appid, max_results)
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

                    elif tool_name == "get_most_expensive_sold_weekly":
                        appid = arguments.get("appid")
                        max_results = arguments.get("max_results", 10)

                        if not appid:
                            resp = {
                                "jsonrpc": "2.0",
                                "id": id_,
                                "error": {
                                    "code": -32602,
                                    "message": "Invalid params: appid is required"
                                }
                            }
                        else:
                            # Validate max_results
                            if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
                                max_results = 10

                            result = get_most_expensive_sold_weekly(appid, max_results)
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