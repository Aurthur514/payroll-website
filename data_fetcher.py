import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from api_wrapper import CoinSwitchAPI
from config import EXCHANGE

class DataFetcher:
    def __init__(self):
        self.api = CoinSwitchAPI()
        self.exchange = EXCHANGE

    def get_candles(self, symbol, resolution='1h', days=30):
        """
        Fetch candlestick data for the last 'days' days.
        resolution: '1h', etc.
        """
        # Map symbol to yfinance format, assuming INR pairs are not available, use USD equivalent
        yahoo_symbol = symbol.replace('/INR', '-USD')
        df = yf.download(yahoo_symbol, period=f'{days}d', interval='1h')
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df.index.name = 'timestamp'
        df = df.astype(float)
        return df

    def get_current_price(self, symbol):
        try:
            ticker = self.api.get_ticker(self.exchange, symbol)
            if ticker and 'data' in ticker and self.exchange in ticker['data']:
                price = float(ticker['data'][self.exchange]['lastPrice'])
                return price
            else:
                print(f"Warning: Invalid ticker data for {symbol}")
                return None
        except Exception as e:
            print(f"Error getting current price for {symbol}: {e}")
            return None

    def get_order_book(self, symbol):
        return self.api.get_order_book(self.exchange, symbol)

    def get_recent_trades(self, symbol, limit=100):
        trades = self.api.get_recent_trades(self.exchange, symbol)
        return trades[:limit] if len(trades) > limit else trades

    def get_trade_info(self, symbol):
        try:
            return self.api.get('/trade/api/v2/tradeInfo', {'exchange': self.exchange, 'symbol': symbol})
        except Exception as e:
            print(f"Error getting trade info for {symbol}: {e}")
            return {'min_quantity': 0.00001, 'max_quantity': 1000}  # Default values

    def get_all_symbols(self):
        try:
            coins = self.api.get_coins(self.exchange)
            if coins and 'data' in coins:
                all_symbols = coins['data'].get(self.exchange, [])
                # Filter for INR pairs
                inr_symbols = [s for s in all_symbols if s.endswith('/INR')]
                return inr_symbols
            else:
                print("Warning: Invalid coins data")
                return []
        except Exception as e:
            print(f"Error getting all symbols: {e}")
            return []

    def get_high_volume_symbols(self, min_volume=10000000):  # 10M USD
        try:
            tickers = self.api.get_all_pairs_ticker(self.exchange)
            if not tickers or 'data' not in tickers:
                print("Warning: Invalid tickers data")
                return []
            
            high_vol_symbols = []
            for symbol, data in tickers['data'].items():
                try:
                    volume = float(data.get('quoteVolume', 0))  # Assuming quoteVolume is in INR or USD equivalent
                    if volume >= min_volume:
                        high_vol_symbols.append(symbol)
                except:
                    pass
            return high_vol_symbols
        except Exception as e:
            print(f"Error getting high volume symbols: {e}")
            return []

    def get_btc_trend(self):
        # Use yfinance to get BTC trend
        import yfinance as yf
        btc = yf.Ticker('BTC-USD')
        hist = btc.history(period='1d', interval='1h')
        if len(hist) < 2:
            return 'unknown'
        recent_prices = hist['Close'].tail(4)  # last 4 hours
        if recent_prices.iloc[-1] > recent_prices.iloc[0]:
            return 'rising'
        elif recent_prices.iloc[-1] < recent_prices.iloc[0]:
            return 'falling'
        else:
            return 'stable'