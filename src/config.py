import requests
import re
import random

SOURCE_URL = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&includeAdjustedClose=true"

DEFAULT_TICKER = "AAPL"
T1_DEFAULT_START = "21.06.2020"

T2_DEFAULT_START = "22.06.2020"
DEFAULT_END = "22.06.2021"
# Alternatively to Default End
RUN_TEST_FOR = 1000
# Minimum Hold: Investment Horizon
HOLD_PERIOD = 180
# Historical Data Period: Get X days historical data from before start
HIST_DATA = 365


# Moving Average Window-Lenght for MA of daily average price
SMA_INTERVAL = 50
# Average to be used in Relative Strength Index
RSI_INTERVAL = 50
OVERBOUGHT_LIMIT = 70
OVERSOLD_LIMIT = 45

# Volatility Multiplier: Use x percent of the volatility
VOL_MULTIPLIER = 0.9

# MACD Configuration: Moving Average Convergence Divergence 
MACD_INTERVALS = [12,26]
MACD_SIGNAL_INTERVAL = 9

# Watchlist: List of stock ticker:
NUM_STOCKS = 50

def random_stock_tickers(n=NUM_STOCKS):
    # Stock list provided by: https://github.com/RayBB ON https://github.com/RayBB/random-stock-picker
    stock_list_url = "https://github.com/RayBB/random-stock-picker/blob/master/stocks.json"
    res = requests.get(stock_list_url).content.decode("utf-8")
    # Isolate relevant HTML
    res = re.search(r'(<td id="LC1"(.+?)td>)', res).group()
    # Get stock list from inner content
    tickers = re.findall(r'(\;[A-Z]+\&)', res)
    # Trim ; and & for only the ticker
    tickers = [x[1:-1] for x in tickers]
    return random.sample(tickers, k=n)
    
WATCHLIST = random_stock_tickers()

# Portfolio
BUDGET = 1000000