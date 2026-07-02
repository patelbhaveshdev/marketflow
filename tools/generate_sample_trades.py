#!/usr/bin/env python3
"""Generate realistic OMS-style trade JSON for local pipeline runs.

Produces the same shape the Databricks bronze layer expects:
- trade amendments (same trade_id, higher version) to exercise dedupe
- a configurable percentage of bad records to exercise the quarantine path

Usage:
    python tools/generate_sample_trades.py --count 500 --out data/sample/trades_$(date +%Y%m%d).json
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SYMBOLS = ["AAPL", "MSFT", "JPM", "GS", "TSLA", "NVDA", "SPY", "QQQ", "XOM", "BAC"]
DESKS = ["EQ-CASH-NY", "EQ-DERIV-NY", "FI-RATES-NY", "PB-CLIENT-NJ"]
PRICE_RANGE = {"AAPL": (180, 240), "MSFT": (380, 470), "JPM": (180, 250),
               "GS": (400, 560), "TSLA": (170, 320), "NVDA": (95, 150),
               "SPY": (520, 610), "QQQ": (440, 540), "XOM": (100, 130), "BAC": (35, 48)}


def make_trade(rng: random.Random, seq: int, day: datetime) -> dict:
    symbol = rng.choice(SYMBOLS)
    low, high = PRICE_RANGE[symbol]
    executed = day.replace(
        hour=rng.randint(9, 16), minute=rng.randint(0, 59),
        second=rng.randint(0, 59), microsecond=0)
    return {
        "trade_id": f"T{day:%Y%m%d}-{seq:06d}",
        "version": 1,
        "symbol": symbol,
        "side": rng.choice(["BUY", "SELL"]),
        "quantity": rng.choice([100, 200, 250, 500, 1000, 2500, 5000]),
        "price": round(rng.uniform(low, high), 4),
        "executed_at": executed.isoformat(),
        "desk": rng.choice(DESKS),
    }


def corrupt(rng: random.Random, trade: dict) -> dict:
    """Return a record that should land in quarantine."""
    bad = dict(trade)
    choice = rng.choice(["neg_qty", "zero_price", "bad_side", "no_timestamp"])
    if choice == "neg_qty":
        bad["quantity"] = -abs(bad["quantity"])
    elif choice == "zero_price":
        bad["price"] = 0
    elif choice == "bad_side":
        bad["side"] = "HOLD"
    else:
        bad["executed_at"] = None
    return bad


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--amend-rate", type=float, default=0.10,
                        help="Fraction of trades that receive a v2 amendment.")
    parser.add_argument("--bad-rate", type=float, default=0.05,
                        help="Fraction of bad records (quarantine path).")
    parser.add_argument("--date", type=str, default=None, help="Trade date YYYY-MM-DD (default: today)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    day = (datetime.strptime(args.date, "%Y-%m-%d") if args.date
           else datetime.now()).replace(tzinfo=timezone.utc)

    trades = [make_trade(rng, i + 1, day) for i in range(args.count)]

    # amendments: bump version, tweak price/quantity (exercises dedupe window)
    for trade in rng.sample(trades, int(args.count * args.amend_rate)):
        amended = dict(trade)
        amended["version"] = 2
        amended["price"] = round(trade["price"] * rng.uniform(0.995, 1.005), 4)
        trades.append(amended)

    # bad records (exercises quarantine)
    trades.extend(corrupt(rng, rng.choice(trades)) for _ in range(int(args.count * args.bad_rate)))

    rng.shuffle(trades)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as fh:
        for trade in trades:  # JSON Lines: one object per line, as OMS drops arrive
            fh.write(json.dumps(trade) + "\n")

    print(f"Wrote {len(trades)} records ({args.count} trades, "
          f"{int(args.count * args.amend_rate)} amendments, "
          f"{int(args.count * args.bad_rate)} bad) -> {args.out}")


if __name__ == "__main__":
    main()
