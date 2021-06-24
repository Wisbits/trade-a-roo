from src.config import WATCHLIST, BUDGET, SOURCE_URL, DEFAULT_TICKER, T2_DEFAULT_START, DEFAULT_END, RSI_INTERVAL, MACD_SIGNAL_INTERVAL, OVERBOUGHT_LIMIT, OVERSOLD_LIMIT, HIST_DATA, RUN_TEST_FOR

from src.task_two import YahooStockPredict

import pandas as pd
from requests.exceptions import ConnectionError

class Stock(YahooStockPredict):
    
    def __init__(self, ticker=DEFAULT_TICKER, start=T2_DEFAULT_START, end=DEFAULT_END, budget=None):
        super().__init__(ticker=ticker, start=start, end=end)
        self.budget = budget
        
    def assign_budget(self, budget=None):
        self.budget = budget
        
    def run_calculations(self):
        super().run_calculations()
        avg_price = super().latest_input(as_series=True)["AVG"]
        self.quantity = int(self.budget / avg_price)
        
    def leftover_budget(self):
        spent = self.investment_summary["Buy In"] * self.investment_summary["Count"]
        return self.budget - spent

class PortfolioManager:
    
    def __init__(self, budget=BUDGET, watchlist=WATCHLIST):
        self.watchlist = watchlist
        self.portfolio = {}
        self.budget = budget
        
    def initialize_stocks(self):
        portfolio = {}
        for stock in self.watchlist:
            portfolio.update({stock: Stock(ticker=stock)})
        for k,v in portfolio.items():
            tries = 0
            while tries < 5:
                try:
                    v.get_historical_data()
                    self.portfolio.update({k:v})
                    break
                except ValueError:
                    # Ignore stock with missing data
                    break
                except ConnectionError:
                    tries += 1
                    continue
            
    def run_stocks(self):
        portfolio_summary = []
        per_stock_budget = self.budget/len(self.portfolio)
        for ticker, stock in self.portfolio.items():
            self.budget -= per_stock_budget
            stock.assign_budget(per_stock_budget)
            results = stock.run_op()
            if results["Buy In"] is not None:
                self.budget += stock.leftover_budget()
            if results["Buy In"] is None:
                self.budget += per_stock_budget
            portfolio_summary.append(results)
        self.portfolio_summary = pd.DataFrame(portfolio_summary)
    
    def expand_summary(self):
        self.portfolio_summary["Return %"] = ((self.portfolio_summary["Sell Price"] / self.portfolio_summary["Buy In"]) - 1) * 100
        self.portfolio_summary["Realized Profit"].fillna(value=0, inplace=True)
        self.portfolio_summary["Unrealized Profit"].fillna(value=0, inplace=True)
        self.portfolio_summary["Sum Profit in 1000$"] = self.portfolio_summary["Realized Profit"].expanding().sum() * 1000
        self.portfolio_summary["Sum Unrealized Profit"] = self.portfolio_summary["Unrealized Profit"].expanding().sum()
    
    def summary_to_html(self):
        html = self.portfolio_summary.to_html()
        with open("portfolio_summary.html", "w", encoding="utf-8") as f:
            f.write(html)
            
    
    
if __name__ == "__main__":
    
    pm = PortfolioManager()
    pm.initialize_stocks()
    pm.run_stocks()