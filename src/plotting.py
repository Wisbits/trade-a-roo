import datetime as dt
import matplotlib.pyplot as plt

from src.config import OVERBOUGHT_LIMIT, OVERSOLD_LIMIT, MACD_SIGNAL_INTERVAL

def plot_rsi(df):
    plt.axhline(OVERSOLD_LIMIT, color='g', linestyle=':')
    plt.axhline(OVERBOUGHT_LIMIT, color='g', linestyle=':')
    plt.ylabel('RSI')
    plt.plot(df["RSI"])
    plt.show()
    
def plot_summary(df):
    ax1 = plt.subplot(211)
    x = df["Date"]
    y11 = df["Lower_Vol"]
    y12 = df["Upper_Vol"]
    y13 = df["Close"]
    plt.plot(x,y11)
    plt.plot(x,y12)
    plt.plot(x,y13)

    ax2 = ax1.twinx()
    y21 = df["RSI"]
    ax2.plot(x, y21, color="r", linestyle=":")
    plt.subplot(212)
    plt.plot(df["MACD_Diff"], label="MACD_Diff")
    plt.plot(df["9D_EMA_MACD_Diff"], label=f"{MACD_SIGNAL_INTERVAL}D_EMA_MACD")
    plt.legend()
    plt.show()