# Steam Market MCP

A Model Context Protocol (MCP) server that provides tools to fetch Steam Market data including current prices and price history.

## Features

- Fetch current market price of Steam items
- Get price history for the last 10 days
- Support for all Steam applications with market items
- Proper error handling and timeout management

## Available Tools

### get_steam_item_data

Fetches detailed Steam market data for a specific item including current price and price history.

**Parameters:**
- `appid` (string, required): Steam application ID (e.g., '730' for CS:GO, '440' for TF2)
- `item_name` (string, required): Exact name of the item including exterior condition

**Example Usage:**
```json
{
  "appid": "730",
  "item_name": "AK-47 | Redline (Field-Tested)"
}
```

**Response:**
```json
{
  "item_name": "AK-47 | Redline (Field-Tested)",
  "appid": "730",
  "current_price": "$51.59",
  "exterior": "Field-Tested",
  "description": "AK-47 | Redline",
  "last_10_days_prices": [
    {
      "date": "Dec 15 2024 01: +0",
      "price": 52.305,
      "sales": "16"
    }
  ],
  "market_url": "https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Redline%20(Field-Tested)",
  "data_points": 10,
  "status": "success"
}
```

### search_steam_items

Search for items in Steam market by name and get a list of matching items with prices.

**Parameters:**
- `appid` (string, required): Steam application ID (e.g., '730' for CS:GO, '440' for TF2)
- `search_term` (string, required): Search term to find items (e.g., 'AK-47 Redline')
- `max_results` (integer, optional): Maximum number of results to return (default: 10, max: 50)

**Example Usage:**
```json
{
  "appid": "730",
  "search_term": "AK-47 Redline",
  "max_results": 5
}
```

**Response:**
```json
{
  "search_term": "AK-47 Redline",
  "appid": "730",
  "total_results": 8,
  "results": [
    {
      "name": "AK-47 | Redline (Field-Tested)",
      "price": "$51.59",
      "quantity_available": "1,158",
      "market_url": "https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Redline%20(Field-Tested)"
    },
    {
      "name": "AK-47 | Redline (Well-Worn)",
      "price": "$39.35",
      "quantity_available": "62",
      "market_url": "https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Redline%20(Well-Worn)"
    }
  ],
  "status": "success"
}
```

### get_popular_items_24h

Get most popular items in the last 24 hours by scanning the entire Steam market and analyzing real sales volume.

**Parameters:**
- `appid` (string, required): Steam application ID (e.g., '730' for CS:GO, '440' for TF2)
- `max_results` (integer, optional): Maximum number of results to return (default: 10, max: 20)

**How it works:**
1. Scans first 500 items from Steam Market (sorted by quantity/activity)
2. Analyzes sales data for top 100 most active items
3. Returns items with highest 24-hour sales volume

**Example Usage:**
```json
{
  "appid": "730",
  "max_results": 5
}
```

**Response:**
```json
{
  "appid": "730",
  "period": "24_hours",
  "type": "market_scan_popular",
  "results": [
    {
      "name": "AK-47 | Redline (Field-Tested)",
      "current_price": "$51.59",
      "quantity_available": "1,158",
      "sales_24h": 117,
      "total_sales": 2450,
      "market_url": "https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Redline%20(Field-Tested)"
    }
  ],
  "total_scanned": 500,
  "total_analyzed": 100,
  "total_found": 5,
  "status": "success",
  "note": "Based on comprehensive Steam Market scan and sales volume analysis"
}
```

### get_most_expensive_sold_24h

Get most expensive items sold in the last 24 hours by scanning high-value market items and analyzing real sales data.

**Parameters:**
- `appid` (string, required): Steam application ID (e.g., '730' for CS:GO, '440' for TF2)
- `max_results` (integer, optional): Maximum number of results to return (default: 10, max: 20)

**How it works:**
1. Scans first 250 items from Steam Market (sorted by price descending)
2. Filters items worth $10+ and analyzes top 50 most expensive
3. Returns items with highest 24-hour sale prices

**Example Usage:**
```json
{
  "appid": "730",
  "max_results": 3
}
```

**Response:**
```json
{
  "appid": "730",
  "period": "24_hours",
  "type": "market_scan_expensive",
  "results": [
    {
      "name": "★ Karambit | Fade (Factory New)",
      "current_price": "$2,450.00",
      "highest_sale_24h": "$2,650.00",
      "recent_sales_count": 3,
      "market_url": "https://steamcommunity.com/market/listings/730/★%20Karambit%20%7C%20Fade%20(Factory%20New)"
    }
  ],
  "total_scanned": 250,
  "total_analyzed": 50,
  "total_found": 3,
  "status": "success",
  "note": "Based on comprehensive Steam Market scan for high-value sales"
}
```

### get_most_expensive_sold_weekly

Get most expensive items available for sale (weekly high-value items) with comprehensive price analysis.

**Parameters:**
- `appid` (string, required): Steam application ID (e.g., '730' for CS:GO, '440' for TF2)
- `max_results` (integer, optional): Maximum number of results to return (default: 10, max: 20)

**Supported Games:**
- `730`: Counter-Strike 2 (CS:GO)
- `440`: Team Fortress 2
- `570`: Dota 2

**Example Usage:**
```json
{
  "appid": "730",
  "max_results": 3
}
```

**Response:**
```json
{
  "appid": "730",
  "period": "weekly",
  "type": "most_expensive_available",
  "results": [
    {
      "name": "★ Karambit | Case Hardened (Factory New)",
      "current_price": "$15,000.00",
      "quantity_available": "1",
      "weekly_sales": 2,
      "highest_weekly_price": "$16,500.00",
      "average_weekly_price": "$15,750.00",
      "market_url": "https://steamcommunity.com/market/listings/730/★%20Karambit%20%7C%20Case%20Hardened%20(Factory%20New)"
    }
  ],
  "total_analyzed": 20,
  "total_found": 3,
  "status": "success",
  "note": "Based on weekly price analysis of ultra high-value items"
}
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the MCP server:
```bash
python server.py
```

## Common Steam App IDs

- Counter-Strike 2: `730`
- Team Fortress 2: `440`
- Dota 2: `570`
- Rust: `252490`
- PUBG: `578080`

## Error Handling

The server includes comprehensive error handling for:
- Network timeouts
- Invalid Steam responses
- Malformed requests
- Missing required parameters
