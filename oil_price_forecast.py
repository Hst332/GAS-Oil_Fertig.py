#!/usr/bin/env python3
"""
oil_price_forecast.py
Ruhige, robuste Go-Live Version (A)

- Brent (BZ=F) & WTI (CL=F) von Yahoo Finance
- Einfaches Trend- + Momentum-Modell
- Saubere Wahrscheinlichkeitslogik
- Signal nur bei klarer Edge
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# =====================
# CONFIG
# =====================
START_DATE = "2010-01-01"
BRENT_SYMBOL = "BZ=F"
WTI_SYMBOL = "CL=F"
PROB_THRESHOLD = 0.57

OUTPUT_FILE = "oil_forecast_output.txt"

# =====================
# LOAD DATA
# =====================
def load_prices():
    brent = yf.download(BRENT_SYMBOL, start=START_DATE, progress=False)
    wti   = yf.download(WTI_SYMBOL, start=START_DATE, progress=False)

    if brent.empty or wti.empty:
        raise RuntimeError("Yahoo returned no data")

    df = pd.DataFrame({
        "Brent": brent["Close"],
        "WTI": wti["Close"]
    }).dropna()

    return df

# =====================
# FEATURE ENGINEERING
# =====================
def build_features(df):
    df = df.copy()

    df["Brent_ret"] = df["Brent"].pct_change()
    df["WTI_ret"] = df["WTI"].pct_change()

    df["Momentum_5"] = df["Brent"].pct_change(5)
    df["SMA_50"] = df["Brent"].rolling(50).mean()
    df["Trend"] = (df["Brent"] > df["SMA_50"]).astype(int)

    df["Target"] = (df["Brent_ret"].shift(-1) > 0).astype(int)

    return df.dropna()

# =====================
# MODEL (LOGIC A)
# =====================
def compute_probability(row):
    prob = 0.5

    if row["Momentum_5"] > 0:
        prob += 0.06
    else:
        prob -= 0.06

    if row["Trend"] == 1:
        prob += 0.05
    else:
        prob -= 0.05

    return max(0.0, min(1.0, prob))

# =====================
# MAIN
# =====================
def main():
    df = load_prices()
    df = build_features(df)

    last = df.iloc[-1]
    prob_up = compute_probability(last)
    prob_down = 1 - prob_up

    signal = "NO_TRADE"
    if prob_up >= PROB_THRESHOLD:
        signal = "UP"
    elif prob_down >= PROB_THRESHOLD:
        signal = "DOWN"

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines.append("===================================")
    lines.append("      OIL PRICE FORECAST (A)")
    lines.append("===================================")
    lines.append(f"Run time (UTC): {now}")
    lines.append(f"Data date     : {df.index[-1].date()}")
    lines.append("")
    lines.append("Sources:")
    lines.append(f"  Brent : Yahoo {BRENT_SYMBOL}")
    lines.append(f"  WTI   : Yahoo {WTI_SYMBOL}")
    lines.append("")
    lines.append(f"Brent Close : {last['Brent']:.2f}")
    lines.append(f"WTI Close   : {last['WTI']:.2f}")
    lines.append("")
    lines.append(f"Probability UP   : {prob_up:.2%}")
    lines.append(f"Probability DOWN : {prob_down:.2%}")
    lines.append("")
    lines.append(f"Signal : {signal}")
    lines.append("===================================")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))
    print(f"\n[OK] Written to {OUTPUT_FILE}")

# =====================
# ENTRYPOINT
# =====================
if __name__ == "__main__":
    main()
