[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/ilkeradanur-steamtools-mcp-badge.png)](https://mseep.ai/app/ilkeradanur-steamtools-mcp)

# Steam Market MCP

A Model Context Protocol (MCP) server that provides tools to fetch Steam Market data including current prices and price history with hybrid real-time scanning capabilities.

## Features

- **Hybrid Real-time Market Scanning**: Dynamic discovery of popular items beyond static databases
- **Comprehensive High-value Items Analysis**: 30 CS:GO, 10 TF2, and 8 Dota 2 high-value items with real sales data
- **Intelligent Rate Limiting**: Optimized to avoid Steam API limits while maximizing data coverage
- **Enhanced Sales Data Extraction**: Robust price history analysis with average price calculations
- **Real-time Popular Items Discovery**: Multiple scanning strategies for comprehensive market coverage
- Fetch current market price of Steam items
- Get price history for the last 10 days
- Support for all Steam applications with market items
- Comprehensive error handling and fallback mechanisms

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

Get most popular items in the last 24 hours using hybrid approach: real-time market scanning + seed items for comprehensive coverage.

**Parameters:**
- `appid` (string, required): Steam application ID (e.g., '730' for CS:GO, '440' for TF2)
- `max_results` (integer, optional): Maximum number of results to return (default: 10, max: 20)

**Enhanced Hybrid Methodology:**
1. **Multi-strategy Market Scan**: Uses 3 different sorting strategies (quantity, price, alphabetical) for comprehensive discovery
2. **Intelligent Rate Limiting**: Optimized delays to avoid Steam API limits while maximizing coverage
3. **Seed Items Integration**: Combines market scan with curated high-activity items database
4. **Real Sales Analysis**: Analyzes top 30 items with actual sales data from Steam market pages
5. **Comprehensive Coverage**: Discovers items beyond predefined lists for true market insights

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
  "type": "hybrid_scan_popular",
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
  "note": "Based on hybrid market scan and sales volume analysis with real-time discovery"
}
```

### get_most_expensive_sold_24h

Get most expensive items sold in the last 24 hours with comprehensive high-value items analysis and enhanced sales data extraction.

**Parameters:**
- `appid` (string, required): Steam application ID (e.g., '730' for CS:GO, '440' for TF2)
- `max_results` (integer, optional): Maximum number of results to return (default: 10, max: 20)

**Enhanced Methodology:**
1. **Comprehensive High-value Database**: Analyzes curated database of proven high-value items
2. **Robust Sales Data Extraction**: Multiple JavaScript patterns for reliable price history parsing
3. **Enhanced Error Handling**: Fallback mechanisms for reliable data extraction
4. **Average Price Calculation**: Provides both highest and average sale prices for better insights
5. **Volume Analysis**: Tracks total sales volume and transaction counts

**Supported Games with Expanded Databases:**
- `730`: CS:GO/CS2 (30 high-value items: ultra-rare knives, legendary skins, high-value gloves)
- `440`: TF2 (10 high-value items: unusual hats, australium weapons, golden items)
- `570`: Dota 2 (8 high-value items: immortals, arcanas, rare couriers)

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
  "type": "comprehensive_expensive_items_analysis",
  "results": [
    {
      "name": "★ Karambit | Fade (Factory New)",
      "current_price": "$2,450.00",
      "highest_sale_24h": "$2,650.00",
      "average_sale_24h": "$2,500.00",
      "recent_sales_count": 3,
      "total_volume_24h": 3,
      "price_data_points": 24,
      "market_url": "https://steamcommunity.com/market/listings/730/★%20Karambit%20%7C%20Fade%20(Factory%20New)"
    }
  ],
  "total_analyzed": 30,
  "total_found": 3,
  "items_with_sales_data": 2,
  "status": "success",
  "methodology": "Analyzes 30 CS:GO, 10 TF2, and 8 Dota 2 high-value items with real market sales data",
  "note": "Enhanced analysis with comprehensive high-value items database and robust sales data extraction"
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
