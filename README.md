# Steam Market MCP

A Model Context Protocol (MCP) server that provides tools to fetch Steam Market data including current prices and price history.

## Features

- Fetch current market price of Steam items
- Get price history for the last 10 days
- Support for all Steam applications with market items
- Proper error handling and timeout management

## Available Tools

### get_steam_item_data

Fetches Steam market item data including current price and price history.

**Parameters:**
- `appid` (string, required): Steam application ID (e.g., '730' for CS:GO, '440' for TF2)
- `item_name` (string, required): Name of the item to search for in the Steam market

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
  "current_price": "$12.34",
  "last_10_days_prices": [
    {
      "date": "Dec 15 2024 01: +0",
      "price": 12.34,
      "sales": 5
    }
  ],
  "market_url": "https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Redline%20(Field-Tested)"
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
