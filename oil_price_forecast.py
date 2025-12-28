#!/usr/bin/env python3
"""
oil_price_forecast.py

CODE A – Ruhig, robust, professionell
- Brent & WTI von Yahoo Finance
- Brent–WTI Spread
- Kein ML, kein sklearn
- TXT Output (überschreibt jedes Mal)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

# -----------------------
# Config
# -----------------------
START_DATE = "2015-01-01"
BRENT_SYMBOL = "BZ=F"
WTI_SYMBOL = "CL=F"

OUTPUT_TXT = "oil_forecast_output.txt"

# -----------------------
# Load data
# -----------------------
def load_prices():
    brent = yf.download(BRENT_SYMBOL, start=START_DATE, progress=False)
    wti = yf.download(WTI_SYMBOL, start=START_DATE, progress=False)

    if brent.empty or wti.empty:
        raise RuntimeError("Yahoo returned empty data")

    df = pd.DataFrame({
        "Brent": brent["Close"],
        "WTI": wti["Close"]
    }).dropna()

    return df

# -----------------------
# Forecast logic (CODE A)
# -----------------------
def compute_forecast(df: pd.DataFrame) -> dict:
    df = df.copy()

    # Returns
    df["Brent_ret"] = df["Brent"].pct_change()
    df["WTI_ret"] = df["WTI"].pct_change()

    # Spread
    df["Spread"] = df["Brent"] - df["WTI"]
    df["Spread_change"] = df["Spread"].diff()

    df = df.dropna()

    last = df.iloc[-1]

    prob_up = 0.50

    # Trend contribution
    if last["Brent_ret"] > 0:
        prob_up += 0.015
    else:
        prob_up -= 0.015

    if last["WTI_ret"] > 0:
        prob_up += 0.015
    else:
        prob_up -= 0.015

    # Spread logic
    if last["Spread_change"] > 0:
        prob_up += 0.01
    else:
        prob_up -= 0.01

    # Clamp
    prob_up = max(0.45, min(0.55, prob_up))
    prob_down = 1.0 - prob_up

    # Signal
    if prob_up >= 0.57:
        signal = "UP"
    elif prob_up <= 0.43:
        signal = "DOWN"
    else:
        signal = "NO_TRADE"

    return {
        "prob_up": prob_up,
        "prob_down": prob_down,
        "signal": signal,
        "data_date": last.name.date().isoformat(),
        "brent": float(last["Brent"]),
        "wti": float(last["WTI"]),
        "spread": float(last["Spread"]),
    }

# -----------------------
# Output
# -----------------------
def write_txt(result: dict):
    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "===================================",
        "   OIL FORECAST – BRENT / WTI (A)",
        "===================================",
        f"Run time (UTC): {now_utc}",
        f"Data date     : {result['data_date']}",
        "",
        f"Brent Close   : {result['brent']:.2f}",
        f"WTI Close     : {result['wti']:.2f}",
        f"Brent–WTI Spd : {result['spread']:.2f}",
        "",
        f"Prob UP       : {result['prob_up']*100:.2f}%",
        f"Prob DOWN     : {result['prob_down']*100:.2f}%",
        f"Signal        : {result['signal']}",
        "===================================",
    ]

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# -----------------------
# Main
# -----------------------
def main():
    df = load_prices()
    result = compute_forecast(df)
    write_txt(result)
    print("[OK] Oil forecast written to", OUTPUT_TXT)

if __name__ == "__main__":
    main()
