import json
import time
import os
from datetime import datetime, timezone

import requests

BASE = "https://data-api.polymarket.com"
TOP_N = 40
TIME_PERIOD = "ALL"
MAX_TRADES_PER_TRADER = 500
PAGE_SIZE = 100


def get(path, params, retries=5):
    for attempt in range(retries):
        r = requests.get(f"{BASE}{path}", params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Gave up on {path} after {retries} tries")


def fetch_leaderboard():
    rows = get("/v1/leaderboard", {
        "category": "POLITICS",
        "timePeriod": TIME_PERIOD,
        "orderBy": "PNL",
        "limit": TOP_N,
    })
    return [{
        "rank": int(row.get("rank", i + 1)),
        "wallet": row.get("proxyWallet") or row.get("user_id"),
        "username": row.get("userName") or row.get("user_name"),
        "pnl": row.get("pnl"),
        "volume": row.get("vol") or row.get("volume"),
        "verified": row.get("verifiedBadge") or row.get("verified"),
    } for i, row in enumerate(rows)]


def fetch_trades(wallet):
    trades, offset = [], 0
    while len(trades) < MAX_TRADES_PER_TRADER:
        page = get("/trades", {"user": wallet, "limit": PAGE_SIZE, "offset": offset})
        if not page:
            break
        trades.extend(page)
        offset += PAGE_SIZE
        time.sleep(0.3)
    return trades[:MAX_TRADES_PER_TRADER]


def main():
    traders = fetch_leaderboard()
    all_trades = []
    for t in traders:
        print(f"Fetching trades for #{t['rank']} {t['username'] or t['wallet']}")
        for tr in fetch_trades(t["wallet"]):
            all_trades.append({
                "wallet": t["wallet"],
                "username": t["username"],
                "timestamp": tr.get("timestamp"),
                "side": tr.get("side"),
                "market": tr.get("title"),
                "outcome": tr.get("outcome"),
                "size": tr.get("size"),
                "price": tr.get("price"),
                "event_slug": tr.get("eventSlug"),
                "tx_hash": tr.get("transactionHash"),
            })
        time.sleep(0.5)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "category": "POLITICS",
        "time_period": TIME_PERIOD,
        "traders": traders,
        "trades": all_trades,
    }
    os.makedirs("data", exist_ok=True)
    with open("data/traders.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {len(traders)} traders and {len(all_trades)} trades")


if __name__ == "__main__":
    main()
