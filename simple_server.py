#!/usr/bin/env python3
"""
Simple MCP server for Steam Market data - Smithery compatible
"""
import sys
import json
import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

def fetch_item_data(appid, item_name):
    """Fetch Steam market item data"""
    try:
        import urllib.parse
        encoded_item_name = urllib.parse.quote(item_name)
        url = f"https://steamcommunity.com/market/listings/{appid}/{encoded_item_name}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"error": f"Failed to fetch data: HTTP {response.status_code}"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get current price
        current_price = "N/A"
        price_span = soup.select_one("span.market_listing_price_with_fee")
        if price_span:
            current_price = price_span.text.strip()
        
        return {
            "item_name": item_name,
            "appid": appid,
            "current_price": current_price,
            "market_url": url,
            "status": "success"
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

def search_steam_items(appid, search_term, max_results=10):
    """Search Steam market items"""
    try:
        search_url = "https://steamcommunity.com/market/search/render/"
        params = {
            'query': search_term,
            'start': 0,
            'count': max_results,
            'appid': appid,
            'norender': 1
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"error": f"Search failed: HTTP {response.status_code}"}
        
        data = response.json()
        if not data.get('success'):
            return {"error": "Search request failed"}
        
        results = []
        if 'results_html' in data and data['results_html']:
            soup = BeautifulSoup(data['results_html'], 'html.parser')
            items = soup.find_all('a', class_='market_listing_row_link')
            
            for item in items[:max_results]:
                name_elem = item.find('span', class_='market_listing_item_name')
                price_elem = item.find('span', class_='normal_price')
                
                if name_elem:
                    results.append({
                        "name": name_elem.text.strip(),
                        "price": price_elem.text.strip() if price_elem else "N/A",
                        "market_url": item.get('href', '')
                    })
        
        return {
            "search_term": search_term,
            "appid": appid,
            "results": results,
            "status": "success"
        }
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

def main():
    """Simple MCP server main loop"""
    logging.info("Starting Simple Steam MCP Server...")
    
    try:
        for line in sys.stdin:
            try:
                line = line.strip()
                if not line:
                    continue
                
                req = json.loads(line)
                method = req.get("method")
                id_ = req.get("id")
                
                if method == "initialize":
                    resp = {
                        "jsonrpc": "2.0",
                        "id": id_,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {
                                "name": "steamtools-mcp",
                                "version": "1.4.0"
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
                                    "description": "Get Steam market data for a specific item",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "appid": {"type": "string", "description": "Steam app ID"},
                                            "item_name": {"type": "string", "description": "Item name"}
                                        },
                                        "required": ["appid", "item_name"]
                                    }
                                },
                                {
                                    "name": "search_steam_items",
                                    "description": "Search Steam market items",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "appid": {"type": "string", "description": "Steam app ID"},
                                            "search_term": {"type": "string", "description": "Search term"},
                                            "max_results": {"type": "integer", "description": "Max results", "default": 10}
                                        },
                                        "required": ["appid", "search_term"]
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
                        result = fetch_item_data(
                            arguments.get("appid"),
                            arguments.get("item_name")
                        )
                        resp = {
                            "jsonrpc": "2.0",
                            "id": id_,
                            "result": {
                                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                            }
                        }
                        
                    elif tool_name == "search_steam_items":
                        result = search_steam_items(
                            arguments.get("appid"),
                            arguments.get("search_term"),
                            arguments.get("max_results", 10)
                        )
                        resp = {
                            "jsonrpc": "2.0",
                            "id": id_,
                            "result": {
                                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                            }
                        }
                        
                    else:
                        resp = {
                            "jsonrpc": "2.0",
                            "id": id_,
                            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                        }
                        
                else:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": id_,
                        "error": {"code": -32601, "message": f"Unknown method: {method}"}
                    }
                
                print(json.dumps(resp))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                error_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                print(json.dumps(error_resp))
                sys.stdout.flush()
                
    except Exception as e:
        logging.error(f"Server error: {e}")

if __name__ == "__main__":
    main()
