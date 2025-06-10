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
