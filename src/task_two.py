from src.config import SOURCE_URL, DEFAULT_TICKER, T2_DEFAULT_START, DEFAULT_END, RSI_INTERVAL, MACD_SIGNAL_INTERVAL, OVERBOUGHT_LIMIT, OVERSOLD_LIMIT, HIST_DATA, RUN_TEST_FOR
from src.task_one import YahooStock, date_to_timestamp
from src import financial as fin

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 
import requests
import io, sys
import math

import logging

handler = logging.StreamHandler(sys.stdout)

logger = logging.getLogger(__name__)
logger.addHandler(handler)

class RealTimeCsvFeed:
    
    def __init__(self, ticker=DEFAULT_TICKER, start=T2_DEFAULT_START, end=DEFAULT_END):
        data_source = SOURCE_URL.format(ticker, date_to_timestamp(start), date_to_timestamp(end))
        data = requests.get(data_source).content
        self.f = io.StringIO(data.decode("utf-8"))
        self.data = self.f.readlines()
        self.header = [x.replace(" ", "_") for x in self.data[0].strip().split(",")]
        # Skip header line
        self.index = 1
        
    def has_next(self):
        try:
            current = self.data[self.index]
            return True
        except IndexError:
            return False
            
    def next(self):
        try:
            current = self.data[self.index]
            self.index += 1
        except IndexError:
            logging.error("Data source is depleted.")
            return None
        data = current.strip().split(",")
        row = pd.DataFrame([data], columns=self.header, dtype="float")
        row["Date"] = pd.to_datetime(row["Date"], "raise", format="%Y-%m-%d")
        return row

def pre_init(days=365, ticker=DEFAULT_TICKER, start=T2_DEFAULT_START, end=DEFAULT_END):
    y = YahooStockPredict(ticker=ticker, start=start, end=end)
    for i in range(days):
        result = y.update_data()
        if result != "error":
            # update_data will return "error" if there is no more data trading left
            y.move_cursor()
    y.row_cursor -= 1
    return y

class YahooStockPredict(YahooStock):
    
    def __init__(self, ticker=DEFAULT_TICKER, start=T2_DEFAULT_START, end=DEFAULT_END):
        # Simulate real time data fetching api
        self.ticker = ticker
        self.horizon_start = datetime.strptime(T2_DEFAULT_START, "%d.%m.%Y")
        self.horizon_end = datetime.strptime(DEFAULT_END, "%d.%m.%Y")
        self.original_row = 0
        self.row_cursor = 0
        self.quantity = 1
        
        self.investment_summary = {
            "Ticker": self.ticker,
            "Horizon Start": self.horizon_start,
            "Horizon End": self.horizon_end,
            
            "Buy Date": None, 
            "Buy In": None, 
            "Count": None,
            "Buying Total": None,
            
            "Sell Date": None,
            "Sell Price": None,
            "Selling Total": None,
            "Realized Profit": None,
            
            "Last Price": None,
            "Last Total": None,
            "Investment Length": None,
            "Unrealized Profit": None,
        }
        
    def get_historical_data(self):
        hist_data_start = self.horizon_start - timedelta(days=HIST_DATA)
        # Initialize YahooStock from task_one for final difference calculation on ROI
        self._stock = YahooStock(self.ticker, start=self.horizon_start.strftime("%d.%m.%Y"), end=self.horizon_end.strftime("%d.%m.%Y"))
        # Get historical data from X days before the investment horizon
        self.hist_data = YahooStock(self.ticker, start=hist_data_start.strftime("%d.%m.%Y"), end=self.horizon_start.strftime("%d.%m.%Y")).data
        logging.info(f"Historial Data Initialized: {self.ticker}  {hist_data_start} --> {self.horizon_start}  {len(self.hist_data)}")
        # Move to cursor to first row in the investment horizon
        self.horizon_start_row = len(self.hist_data)
        self.row_cursor = len(self.hist_data)
        
    def initialize_feed(self):
        self.api = RealTimeCsvFeed(self.ticker, self.horizon_start.strftime("%d.%m.%Y"), self.horizon_end.strftime("%d.%m.%Y"))
        
    def fetch_feed(self):
        row = self.api.next()
        if row is None:
            logging.info(f"Fetched row is None at {self.row_cursor}")
        self.hist_data = self.hist_data.append([row], ignore_index=True)
        
    def run_calculations(self):
        df = self.hist_data
        df = fin.calc_daily_return(df)
        df = fin.calc_volatility(df, key="Return")
        df = fin.calc_volatility_limits(df)
        df = fin.add_rsi(df)
        df = fin.add_macd(df)
        self.hist_data = df
    
    def latest_input(self, as_series=False): 
        if as_series:
            return self.hist_data.iloc[-1]
        return self.hist_data.iloc[[-1]]
    
    def buy_signal(self):
        latest_input = self.latest_input(as_series=True)
        # When the "signal line" is below the "MACD Diff Line", we have a bullish signal
        macd_bullish = latest_input["MACD_Diff"] > latest_input[f"{MACD_SIGNAL_INTERVAL}D_EMA_MACD_Diff"]
        # When our stock is oversold we have a bullish signal: Constraints can be configured in config
        rsi_signal = latest_input["RSI"] < OVERSOLD_LIMIT
        # When today's price is below (x-days MA price * (1 - volatility))
        # Volatility might be reduced by a "padding"
        volatility_signal = latest_input["Close"] < latest_input["Lower_Vol"]
        return macd_bullish & (rsi_signal | volatility_signal)
    
    def sell_signal(self, only_macd=False):
        latest_input = self.latest_input(as_series=True)
        macd_bearish = latest_input["MACD_Diff"] < latest_input[f"{MACD_SIGNAL_INTERVAL}D_EMA_MACD_Diff"]
        rsi_signal = latest_input["RSI"] > OVERBOUGHT_LIMIT
        volatility_signal = latest_input["Close"] > latest_input["Upper_Vol"]
        if only_macd:
            return macd_bearish
        return macd_bearish & (rsi_signal | volatility_signal)

    def move_cursor(self):
        self.row_cursor += 1
        
    def run_op(self):
        self.get_historical_data()
        self.initialize_feed()
        self.run_calculations()
        
        summ = self.investment_summary
        latest = None
        
        while self.api.has_next():
            if summ["Sell Price"] and summ["Buy In"]:
                break
            self.fetch_feed()
            self.run_calculations()
            buy = self.buy_signal()
            sell = self.sell_signal()
            latest = self.latest_input(as_series=True)
            if buy and summ["Buy In"] is None:
                summ["Buy In"] = latest["AVG"]
                summ["Buy Date"] = latest["Date"]
                summ["Count"] = self.quantity
                summ["Buying Total"] = summ["Buy In"] * summ["Count"]
            if summ["Buy In"]:
                days_holding = latest["Date"] - summ["Buy Date"]
                # After 100 days holding sell at 10% profit the first chance you get (be humble)
                # Before 100 days holding sell at 10% + (10%  -  0.1% x days hold)
                if sell or (latest["AVG"] / summ["Buy In"]) > (1.1 + 0.1 * (1 - 0.01*days_holding.days)):
                    summ["Sell Price"] = latest["AVG"]
                    summ["Sell Date"] = latest["Date"]
                    summ["Selling Total"] = summ["Sell Price"] * summ["Count"]
                    summ["Realized Profit"] = self._stock._calculate_roi(summ["Buy In"], summ["Sell Price"]) * summ["Count"]
            self.move_cursor()
            
        if summ["Buy In"] is None and summ["Sell Price"] is None:
            print(f"{self.ticker}: No investment opportunity.")
        if summ["Buy In"]:
            print(f"{self.ticker}: Bought.")
            if summ["Sell Price"] is None:
                print(f"{self.ticker}: Not sold yet.")
                summ["Last Price"] = latest["Close"]
                summ["Last Total"] = summ["Last Price"] * summ["Count"]
                summ["Investment Length"] = latest["Date"] - summ["Buy Date"]
                summ["Unrealized Profit"] = self._stock._calculate_roi(summ["Buy In"], summ["Last Price"]) * summ["Count"]
        return self.investment_summary
            
        
    def plot_returns(self, incl=["crossover"], smooth=False, interval=3):
        key = "Return"
        if smooth:
            self.calc_moving_avg(key, interval)
            key = f"{str(interval)}MA_{key}"
        plt.plot(self.data["Date"], self.data[key])
        for label in incl:
            if label == "crossover":
                crossing_dates = self.crossings["Date"]
                for date in crossing_dates:
                    plt.axvline(x=date, linestyle=":", color="c")
        plt.show()
        
    def plot_volatility(self):
        fig, ax = plt.subplots()
        self.data["Return"].hist(ax=ax, bins=50, alpha=0.6, color="#8a2f27")
        ax.set_xlabel("Return Rate")
        ax.set_ylabel("Return Frequency")
        ax.set_title(f"{self.ticker} volatility: " + str(round(self.volatility, 4)*100) + "%")
        plt.show()
        
    def plot_cum_volatility(self, keys="10D_CumReturn"):
        plt.figure(figsize=[15,10])
        plt.grid(True)
        if type(keys) == list:
            for i in range(len(keys)):
                plt.subplot(len(keys), 1, i+1)
                plt.title(keys[i])
                plt.hist(self.data[keys[i]], bins=50, alpha=0.6, color="#8a2f27")
        else:
            plt.hist(self.data[keys], bins=50, alpha=0.6, color="#8a2f27")
        plt.show()

if __name__ == "__main__":
    
    y = YahooStockPredict()
    y.get_historical_data()
    y.initialize_feed()
    y.run_calculations()
    
    while y.api.has_next():
        y.fetch_feed()
        y.run_calculations()
        buy = y.buy_signal()
        sell = y.sell_signal()
        if not y.bought:
            if buy:
                y.bought = y.latest_input(as_series=True)["AVG"]
        if y.bought:
            if sell:
                y.sold = y.latest_input(as_series=True)
        if y.bought:
            if sell:
                roi = y.calculate_return(y.bought, y.sold)
                # Calculate difference between 
                diff = roi - y.stock.calculate_return()
                print(diff)
        y.move_cursor()        
        
    if not y.bought and not y.sold:
        print("No investment opportunity.")