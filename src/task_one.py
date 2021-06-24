

"""
1. how you understand it
2. how you initially planned to solve it
3. what obstacles you faced during the solution process and
4. what the actual solution is.
"""


from src.config import SOURCE_URL, DEFAULT_TICKER, T1_DEFAULT_START, DEFAULT_END


from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import requests
import io

SOURCE_URL = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&includeAdjustedClose=true"

def date_to_timestamp(str_date):
    # Yahoo API takes temporal constraints as a timestamp, generally data input is human-readable:
    # to simulate this we will convert an input date string into a timestamp
    dtobj = datetime.strptime(str_date, "%d.%m.%Y")
    # Check if the date is a saturday or sunday
    if dtobj.weekday() >= 5:
        # If date is a saturday or sunday, move to next monday
        diff = 7 - dtobj.weekday()
        dtobj = dtobj + timedelta(days=diff)
    return int(datetime.timestamp(dtobj))

class YahooStock:
    
    def __init__(self, ticker=DEFAULT_TICKER, start=T1_DEFAULT_START, end=DEFAULT_END):
        data_source = SOURCE_URL.format(ticker, date_to_timestamp(start), date_to_timestamp(end))
        data = requests.get(data_source).content
        # Read data into a pandas dataframe
        self.data = pd.read_csv(io.StringIO(data.decode("utf-8")), parse_dates=["Date"])
        self.data.columns = [x.replace(" ", "_") for x in self.data.columns]
        self.calculated_ma = []
        
    def _lowest_entry(self, highest=None):
        if highest is not None:
            # Given a highest point of exit (buying opportunity), get lowest entry before (+1 for inclusion of row with highest)
            to_highest = self.data.iloc[:highest+1]
            return to_highest["Low"].idxmin()
        return self.data["Low"].idxmin()
    
    def _highest_exit(self, lowest=None):
        if lowest is not None:
            # Given a lowest point of entry (buying opportunity), get highest exit afterwards
            from_lowest = self.data.iloc[lowest:]
            return from_lowest["High"].idxmax()
        return self.data["High"].idxmax()
    
    def _price_by_index(self, rowid, key="Low"):
        # Get price by row id and key (type of price)
        return self.data.iloc[rowid][key]
    
    def _calculate_roi(self, initial_value, final_value, investment_costs=0):  
        # Change in percentage from initial value to final value of the equity: Return on Investment
        return (final_value - initial_value - investment_costs) / (initial_value / 100)
    
    def validated_points_of_interest(self):
        global_min = self._lowest_entry()
        global_max = self._highest_exit()
        # Check if the global minimum comes after the global maximum
        if self.data.iloc[global_max]["Date"] < self.data.iloc[global_min]["Date"]:
            # If so, find a local minimum before the global max
            local_min = self._lowest_entry(highest=global_max)
            first_roi = _calculate_roi(self._price_by_index(local_min, key="Low"), self._price_by_index(global_max, key="High"))
            # And a local maximum after the global minimum
            local_max = self._highest_exit(lowest=global_min)
            second_roi = _calculate_roi(self._price_by_index(global_min, key="Low"), self._price_by_index(local_max, key="High"))
            # Return pair with higher ROI
            if second_roi > first_roi:
                return global_min, local_max
            else:
                return local_min, global_max
        else:
            return global_min, global_max
            
    def calculate_return(self, buy=None, sell=None, investment_cost=0):
        if type(buy) is float and type(sell) is float:
            return _calculate_roi(buy, sell, investment_cost)
        if not buy and not sell:
            buy, sell = self.validated_points_of_interest()
        if buy is None:
            buy = self._lowest_entry()
        if sell is None:
            sell = self._highest_exit()
        buying_price = self.data.iloc[buy]["Low"]
        selling_price = self.data.iloc[sell]["High"]
        return _calculate_roi(buying_price, selling_price, investment_cost)

    def plot_columns(self, keys="7MA", no_subplot=False):
        df = self.data.set_index("Date")
        plt.figure(figsize=[15,10])
        plt.grid(True)
        if type(keys) == list:
            if no_subplot is False:
                for i in range(len(keys)):
                    plt.subplot(len(keys), 1, i+1)
                    plt.title(keys[i])
                    plt.plot(df[keys[i]])
            else:
                for k in keys:
                    plt.plot(df[k])
        else:
            plt.plot(df[keys], label=keys)
        plt.legend(loc=2)
        plt.show()

if __name__ == "__main__":
    
    y = YahooStock()
    initial, final = y.validated_points_of_interest()
    roi = y.calculate_return(initial, final)