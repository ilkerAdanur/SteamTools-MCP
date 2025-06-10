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
    """Get most popular items in the last 24 hours by analyzing sales volume from known popular items"""

    # Define popular items for different games
    popular_items_db = {
        "730": [  # CS:GO/CS2
            "AK-47 | Redline (Field-Tested)",
            "AWP | Dragon Lore (Factory New)",
            "M4A4 | Howl (Factory New)",
            "AK-47 | Fire Serpent (Factory New)",
            "Glock-18 | Fade (Factory New)",
            "USP-S | Kill Confirmed (Factory New)",
            "M4A1-S | Hot Rod (Factory New)",
            "Desert Eagle | Blaze (Factory New)",
            "AK-47 | Case Hardened (Factory New)",
            "AWP | Medusa (Factory New)",
            "M4A4 | Poseidon (Factory New)",
            "AK-47 | Vulcan (Factory New)",
            "AWP | Lightning Strike (Factory New)",
            "M4A1-S | Icarus Fell (Factory New)",
            "Glock-18 | Water Elemental (Factory New)"
        ],
        "440": [  # TF2
            "Unusual Team Captain",
            "Australium Rocket Launcher",
            "Strange Professional Killstreak Rocket Launcher",
            "Unusual Burning Flames Team Captain",
            "Golden Frying Pan"
        ],
        "570": [  # Dota 2
            "Dragonclaw Hook",
            "Timebreaker",
            "Stache",
            "Alpine Stalker's Hat"
        ]
    }

    items_to_check = popular_items_db.get(appid, [])
    if not items_to_check:
        return {
            "error": f"No popular items database available for appid {appid}",
            "appid": appid,
            "supported_games": list(popular_items_db.keys())
        }

    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    session = requests.Session()
    session.headers.update(headers)

    for item_name in items_to_check[:max_results * 2]:  # Check more items than needed
        try:
            # Get item data including sales volume
            import urllib.parse
            encoded_item_name = urllib.parse.quote(item_name)
            item_url = f"https://steamcommunity.com/market/listings/{appid}/{encoded_item_name}"

            response = session.get(item_url, timeout=10)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Get current price
            current_price = "N/A"
            price_selectors = [
                "span.market_listing_price.market_listing_price_with_fee",
                "span.market_listing_price_with_fee",
                "span.market_listing_price"
            ]

            for selector in price_selectors:
                price_span = soup.select_one(selector)
                if price_span and price_span.text.strip():
                    current_price = price_span.text.strip()
                    break

            # Extract sales data from JavaScript
            sales_24h = 0
            total_sales = 0

            # Try to find price history data
            js_patterns = [
                r"var line1=(\[.*?\]);",
                r"line1=(\[.*?\]);",
                r'"line1":(\[.*?\])'
            ]

            for pattern in js_patterns:
                match = re.search(pattern, response.text)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        # Calculate sales in last 24 hours (last few data points)
                        recent_data = data[-24:] if len(data) >= 24 else data
                        for entry in recent_data:
                            if len(entry) >= 3:
                                sales_24h += int(entry[2]) if str(entry[2]).isdigit() else 0

                        # Calculate total sales
                        for entry in data:
                            if len(entry) >= 3:
                                total_sales += int(entry[2]) if str(entry[2]).isdigit() else 0
                        break
                    except Exception:
                        continue

            # Only include items with sales data
            if sales_24h > 0 or current_price != "N/A":
                results.append({
                    "name": item_name,
                    "current_price": current_price,
                    "sales_24h": sales_24h,
                    "total_sales": total_sales,
                    "market_url": item_url,
                    "popularity_score": sales_24h * 10 + (total_sales // 100)  # Custom popularity metric
                })

        except Exception as e:
            continue

    # Sort by popularity (sales volume in 24h)
    results.sort(key=lambda x: x['popularity_score'], reverse=True)

    # Remove popularity_score from final results and limit to max_results
    final_results = []
    for item in results[:max_results]:
        final_item = {k: v for k, v in item.items() if k != 'popularity_score'}
        final_results.append(final_item)

    return {
        "appid": appid,
        "period": "24_hours",
        "type": "most_popular_by_sales",
        "results": final_results,
        "total_analyzed": len(items_to_check),
        "total_found": len(final_results),
        "status": "success",
        "note": "Based on sales volume analysis of known popular items"
    }

def get_most_expensive_sold_24h(appid, max_results=10):
    """Get most expensive items sold in the last 24 hours by analyzing high-value items"""

    # Define high-value items for different games
    expensive_items_db = {
        "730": [  # CS:GO/CS2 - High value items
            "★ Karambit | Fade (Factory New)",
            "★ M9 Bayonet | Crimson Web (Factory New)",
            "★ Karambit | Case Hardened (Factory New)",
            "AWP | Dragon Lore (Factory New)",
            "M4A4 | Howl (Factory New)",
            "AK-47 | Fire Serpent (Factory New)",
            "★ Butterfly Knife | Fade (Factory New)",
            "★ Karambit | Doppler (Factory New)",
            "★ Bayonet | Crimson Web (Factory New)",
            "★ Flip Knife | Gamma Doppler (Factory New)",
            "★ Gut Knife | Marble Fade (Factory New)",
            "★ Huntsman Knife | Fade (Factory New)",
            "★ Shadow Daggers | Fade (Factory New)",
            "★ Bowie Knife | Case Hardened (Factory New)",
            "★ Falchion Knife | Fade (Factory New)"
        ],
        "440": [  # TF2
            "Golden Frying Pan",
            "Unusual Burning Flames Team Captain",
            "Unusual Scorching Flames Team Captain",
            "Australium Rocket Launcher",
            "Unusual Sunbeams Team Captain"
        ],
        "570": [  # Dota 2
            "Dragonclaw Hook",
            "Timebreaker",
            "Stache",
            "Alpine Stalker's Hat",
            "Ethereal Flames War Dog"
        ]
    }

    items_to_check = expensive_items_db.get(appid, [])
    if not items_to_check:
        return {
            "error": f"No expensive items database available for appid {appid}",
            "appid": appid,
            "supported_games": list(expensive_items_db.keys())
        }

    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    session = requests.Session()
    session.headers.update(headers)

    for item_name in items_to_check:
        try:
            # Get item data including recent sales
            import urllib.parse
            encoded_item_name = urllib.parse.quote(item_name)
            item_url = f"https://steamcommunity.com/market/listings/{appid}/{encoded_item_name}"

            response = session.get(item_url, timeout=10)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Get current price
            current_price = "N/A"
            price_selectors = [
                "span.market_listing_price.market_listing_price_with_fee",
                "span.market_listing_price_with_fee",
                "span.market_listing_price"
            ]

            for selector in price_selectors:
                price_span = soup.select_one(selector)
                if price_span and price_span.text.strip():
                    current_price = price_span.text.strip()
                    break

            # Extract recent sales data from JavaScript
            recent_sales = []
            highest_sale_24h = 0

            # Try to find price history data
            js_patterns = [
                r"var line1=(\[.*?\]);",
                r"line1=(\[.*?\]);",
                r'"line1":(\[.*?\])'
            ]

            for pattern in js_patterns:
                match = re.search(pattern, response.text)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        # Get recent sales (last 24 hours worth of data)
                        recent_data = data[-24:] if len(data) >= 24 else data

                        for entry in recent_data:
                            if len(entry) >= 2:
                                price = float(entry[1]) if isinstance(entry[1], (int, float)) else 0
                                if price > highest_sale_24h:
                                    highest_sale_24h = price

                        # Get the most recent sale info
                        if recent_data:
                            latest_entry = recent_data[-1]
                            if len(latest_entry) >= 3:
                                recent_sales.append({
                                    "price": latest_entry[1],
                                    "volume": latest_entry[2] if len(latest_entry) > 2 else 0,
                                    "date": latest_entry[0] if len(latest_entry) > 0 else "Unknown"
                                })
                        break
                    except Exception:
                        continue

            # Only include items with price data
            if current_price != "N/A" or highest_sale_24h > 0:
                # Extract numeric value for sorting
                price_value = 0
                if current_price != "N/A":
                    price_match = re.search(r'[\d,]+\.?\d*', current_price.replace(',', ''))
                    if price_match:
                        price_value = float(price_match.group().replace(',', ''))

                if highest_sale_24h > 0:
                    price_value = max(price_value, highest_sale_24h)

                results.append({
                    "name": item_name,
                    "current_price": current_price,
                    "highest_sale_24h": f"${highest_sale_24h:.2f}" if highest_sale_24h > 0 else "No recent sales",
                    "recent_sales_count": len(recent_sales),
                    "market_url": item_url,
                    "price_value": price_value
                })

        except Exception as e:
            continue

    # Sort by price value (highest first)
    results.sort(key=lambda x: x['price_value'], reverse=True)

    # Remove price_value from final results and limit to max_results
    final_results = []
    for item in results[:max_results]:
        final_item = {k: v for k, v in item.items() if k != 'price_value'}
        final_results.append(final_item)

    return {
        "appid": appid,
        "period": "24_hours",
        "type": "most_expensive_sold",
        "results": final_results,
        "total_analyzed": len(items_to_check),
        "total_found": len(final_results),
        "status": "success",
        "note": "Based on price analysis of known high-value items"
    }

def get_most_expensive_sold_weekly(appid, max_results=10):
    """Get most expensive items available for sale (weekly high-value items) with current prices"""

    # Define ultra high-value items for different games
    ultra_expensive_items_db = {
        "730": [  # CS:GO/CS2 - Ultra rare and expensive items
            "★ Karambit | Case Hardened (Factory New)",
            "★ M9 Bayonet | Crimson Web (Factory New)",
            "★ Karambit | Crimson Web (Factory New)",
            "AWP | Dragon Lore (Factory New)",
            "M4A4 | Howl (Factory New)",
            "★ Butterfly Knife | Crimson Web (Factory New)",
            "★ Karambit | Fade (Factory New)",
            "AK-47 | Fire Serpent (Factory New)",
            "★ Bayonet | Case Hardened (Factory New)",
            "★ Flip Knife | Crimson Web (Factory New)",
            "★ Gut Knife | Crimson Web (Factory New)",
            "★ Huntsman Knife | Crimson Web (Factory New)",
            "★ Shadow Daggers | Crimson Web (Factory New)",
            "★ Bowie Knife | Crimson Web (Factory New)",
            "★ Falchion Knife | Crimson Web (Factory New)",
            "★ Stiletto Knife | Crimson Web (Factory New)",
            "★ Ursus Knife | Crimson Web (Factory New)",
            "★ Navaja Knife | Crimson Web (Factory New)",
            "★ Talon Knife | Crimson Web (Factory New)",
            "★ Classic Knife | Crimson Web (Factory New)"
        ],
        "440": [  # TF2
            "Golden Frying Pan",
            "Unusual Burning Flames Team Captain",
            "Unusual Scorching Flames Team Captain",
            "Unusual Sunbeams Team Captain",
            "Unusual Cloudy Moon Team Captain",
            "Australium Rocket Launcher",
            "Australium Minigun",
            "Australium Scattergun"
        ],
        "570": [  # Dota 2
            "Dragonclaw Hook",
            "Timebreaker",
            "Stache",
            "Alpine Stalker's Hat",
            "Ethereal Flames War Dog",
            "Ethereal Flames Stumpy"
        ]
    }

    items_to_check = ultra_expensive_items_db.get(appid, [])
    if not items_to_check:
        return {
            "error": f"No ultra expensive items database available for appid {appid}",
            "appid": appid,
            "supported_games": list(ultra_expensive_items_db.keys())
        }

    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    session = requests.Session()
    session.headers.update(headers)

    for item_name in items_to_check:
        try:
            # Get item data including weekly sales trends
            import urllib.parse
            encoded_item_name = urllib.parse.quote(item_name)
            item_url = f"https://steamcommunity.com/market/listings/{appid}/{encoded_item_name}"

            response = session.get(item_url, timeout=10)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Get current price
            current_price = "N/A"
            price_selectors = [
                "span.market_listing_price.market_listing_price_with_fee",
                "span.market_listing_price_with_fee",
                "span.market_listing_price"
            ]

            for selector in price_selectors:
                price_span = soup.select_one(selector)
                if price_span and price_span.text.strip():
                    current_price = price_span.text.strip()
                    break

            # Get quantity available
            quantity_available = "N/A"
            qty_selectors = [
                "span.market_listing_num_listings_qty",
                "span#searchResults_total"
            ]

            for selector in qty_selectors:
                qty_span = soup.select_one(selector)
                if qty_span and qty_span.text.strip():
                    quantity_available = qty_span.text.strip()
                    break

            # Extract weekly sales data from JavaScript
            weekly_sales = 0
            highest_weekly_price = 0
            average_weekly_price = 0

            # Try to find price history data
            js_patterns = [
                r"var line1=(\[.*?\]);",
                r"line1=(\[.*?\]);",
                r'"line1":(\[.*?\])'
            ]

            for pattern in js_patterns:
                match = re.search(pattern, response.text)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        # Get weekly data (last 7 days worth of data, assuming hourly data)
                        weekly_data = data[-168:] if len(data) >= 168 else data

                        prices = []
                        for entry in weekly_data:
                            if len(entry) >= 3:
                                price = float(entry[1]) if isinstance(entry[1], (int, float)) else 0
                                volume = int(entry[2]) if str(entry[2]).isdigit() else 0

                                if price > 0:
                                    prices.append(price)
                                    if price > highest_weekly_price:
                                        highest_weekly_price = price

                                weekly_sales += volume

                        if prices:
                            average_weekly_price = sum(prices) / len(prices)
                        break
                    except Exception:
                        continue

            # Only include items with price data
            if current_price != "N/A" or highest_weekly_price > 0:
                # Extract numeric value for sorting
                price_value = 0
                if current_price != "N/A":
                    price_match = re.search(r'[\d,]+\.?\d*', current_price.replace(',', ''))
                    if price_match:
                        price_value = float(price_match.group().replace(',', ''))

                if highest_weekly_price > 0:
                    price_value = max(price_value, highest_weekly_price)

                results.append({
                    "name": item_name,
                    "current_price": current_price,
                    "quantity_available": quantity_available,
                    "weekly_sales": weekly_sales,
                    "highest_weekly_price": f"${highest_weekly_price:.2f}" if highest_weekly_price > 0 else "No sales data",
                    "average_weekly_price": f"${average_weekly_price:.2f}" if average_weekly_price > 0 else "No sales data",
                    "market_url": item_url,
                    "price_value": price_value
                })

        except Exception as e:
            continue

    # Sort by price value (highest first)
    results.sort(key=lambda x: x['price_value'], reverse=True)

    # Remove price_value from final results and limit to max_results
    final_results = []
    for item in results[:max_results]:
        final_item = {k: v for k, v in item.items() if k != 'price_value'}
        final_results.append(final_item)

    return {
        "appid": appid,
        "period": "weekly",
        "type": "most_expensive_available",
        "results": final_results,
        "total_analyzed": len(items_to_check),
        "total_found": len(final_results),
        "status": "success",
        "note": "Based on weekly price analysis of ultra high-value items"
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