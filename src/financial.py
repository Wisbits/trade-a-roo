import pandas as pd
import numpy as np
import math

from src.config import RSI_INTERVAL, SMA_INTERVAL, VOL_MULTIPLIER, MACD_INTERVALS, MACD_SIGNAL_INTERVAL

def interval_label(interval, key):
    return f"{str(interval)}D_{key}"

def calc_daily_return(df):
    df["Return"] = np.log(df["Close"] / df["Close"].shift(1))
    return df

def add_cum_returns(df, interval):
    label = interval_label(interval, "CumReturn")
    df[label] = df["Return"].rolling(window=interval).sum()
    return df    

def avg_price(df):
    df["AVG"] = (df["High"] + df["Low"]) / 2
    return df    

        
def add_moving_avg(df, key="Adj_Close", interval=7, matype="SMA", labeled=False):
    label = interval_label(interval, f"{matype}_{key}")
    if matype == "SMA":
        df[label] = df[key].rolling(window=interval).mean()
    elif matype == "EMA":
        # EMA is used for the calculation of RSI, which requires the "Close"-Prices
        df[label] = df[key].ewm(span=interval, min_periods=interval, adjust=False).mean()
    else:
        return df
    if labeled:
        return df, label
    return df

def calc_volatility(df, key="Return"):
    # expanding daily_std x (expanding square root of number of past trading days)
    df["Volatility"] = df[key].expanding().std() * df[key].expanding().count().apply(lambda x: math.sqrt(x))
    return df

def calc_volatility_limits(df, interval=SMA_INTERVAL):
    df = avg_price(df)
    df, label = add_moving_avg(df, key="Close", matype="SMA", interval=interval, labeled=True)
    df["Lower_Vol"] = (df[label] * (1 - ((df["Volatility"] * VOL_MULTIPLIER)/2)))
    df["Upper_Vol"] = (df[label] * (1 + ((df["Volatility"] * VOL_MULTIPLIER)/2)))
    return df

def add_macd(df, intervals=MACD_INTERVALS):
    labels = []
    for i in intervals:
        df, label = add_moving_avg(df, key="Close", interval=i, matype="EMA", labeled=True)
        labels.append(label)
    df["MACD_Diff"] = df[labels[0]] - df[labels[1]]
    df = add_moving_avg(df, key="MACD_Diff", interval=MACD_SIGNAL_INTERVAL, matype="EMA")
    return df

def add_rsi(df, interval=RSI_INTERVAL):
    df["Prev_Close"] = df["Close"].shift(1)
    # Get absolute difference previous and current close:
    df["Up"] = df["Close"] - df["Prev_Close"]
    df["Down"] = df["Prev_Close"] - df["Close"]
    df["Up"] = df["Up"].apply(lambda x: 0 if x < 0 else x)
    df["Down"] = df["Down"].apply(lambda x: 0 if x < 0 else x)
    # Calculate EMA for both possible Trends (upwards and downwards)
    df = add_moving_avg(df, key="Up", interval=interval, matype="EMA")
    df = add_moving_avg(df, key="Down", interval=interval, matype="EMA")
    df["RS"] = df[interval_label(interval, "EMA_Up")] / df[interval_label(interval, "EMA_Down")]
    df["RSI"] = df["RS"].apply(lambda x: (100 - (100 / (1 + x))))
    df = df.drop(columns=["Prev_Close", "Up", "Down", interval_label(interval, "EMA_Up"), interval_label(interval, "EMA_Down")])
    return df
