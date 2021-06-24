from src.task_one import calculate_roi, YahooStock
from src.task_two import pre_init, YahooStockPredict

import matplotlib.pyplot as plt
from src.config import OVERBOUGHT_LIMIT, OVERSOLD_LIMIT, DEFAULT_END, T2_DEFAULT_START, RUN_TEST_FOR

import requests

def random_stock_ticker(n=100):
    stock_list = []
    for x in range(n):
        res = requests.get("https://raybb.github.io/random-stock-picker/")
        

if __name__ == "__main__":
    
    pass
    