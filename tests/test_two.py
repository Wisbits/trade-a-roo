from src.task_two import YahooStockPredict

import unittest
import numpy as np

class TaskTwoTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.stock = YahooStockPredict(ticker="AAPL", start="22.06.2020", end="22.06.2021")
        cls.stock.get_historical_data()
    
    def test_hist_data(self):
        # Check if date parser works as intended
        self.assertIs(self.stock.hist_data["Date"].dtype.type, np.datetime64)
        
    def test_api_next(self):
        self.stock.initialize_feed()
        row = self.stock.api.next()
        self.assertEqual(len(row.columns), 7)
        date_col_num = row.columns.get_loc(key="Date")
        self.assertEqual(date_col_num, 0)
        # Test if there is overlap between historical data and first incoming real-time data
        self.assertNotEqual(row.iloc[0,0], self.stock.hist_data.iloc[-1,0])
        # Check if date parser works as intended
        self.assertIs(row["Date"].dtype.type, np.datetime64)

    def test_latest_input(self):
        latest = self.stock.latest_input()
        self.assertAlmostEqual(latest.iloc[0,0], np.datetime64("2020-06-19"))
        self.assertAlmostEqual(latest.iloc[0,1], 88.660004)
        self.assertAlmostEqual(latest.iloc[0,2], 89.139999)
        self.assertAlmostEqual(latest.iloc[0,3], 86.287498)
        self.assertAlmostEqual(latest.iloc[0,4], 87.430000)
        self.assertAlmostEqual(latest.iloc[0,5], 86.844833)
        self.assertAlmostEqual(latest.iloc[0,6], 264476000.0)








if __name__ == '__main__':
    unittest.main()