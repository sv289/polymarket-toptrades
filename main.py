import json
import time
import requests

LEADERBOARD_URL = "https://data-api.polymarket.com/v2/leaderboard"
TRADES_URL = "https://data-api.polymarket.com/trades"

def get_top_traders(limit=10, window="all"):
    """Fetch top traders sorted by PnL from Polymarket."""
    params = {
        "limit": limit,
        "window": window,
        "sortBy": "pnl"
    }
    try:
        response = requests.get(LEADERBOARD_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching leaderboard: {e}")
        return []

def get_trader_trades(wallet_address, limit=20):
    """Fetch recent trades for a specific proxy/wallet address."""
    params = {
        "user": wallet_address,
        "limit": limit
    }
    try:
        response = requests.get(TRADES_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching trades for {wallet_address}: {e}")
        return []

def main():
    print("Fetching top traders from Polymarket...")
    top_traders = get_top_traders(limit=10, window="all")
    
    trader_data = []

    for trader in top_traders:
        wallet = trader.get("proxyWallet") or trader.get("user")
        name = trader.get("name") or trader.get("username") or wallet
        
        if not wallet:
            continue
            
        print(f"Fetching trades for: {name} ({wallet})...")
        trades = get_trader_trades(wallet, limit=15)
        
        trader_data.append({
            "trader_info": trader,
            "recent_trades": trades
        })
        
        time.sleep(0.5)  # Rate-limiting cushion

    output_filename = "polymarket_top_traders_trades.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(trader_data, f, indent=4)
        
    print(f"Data successfully saved to {output_filename}")

if __name__ == "__main__":
    main()
