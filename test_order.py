from api_wrapper import CoinSwitchAPI
from config import EXCHANGE

EXCHANGE_TEST = 'COINSWITCH'  # try uppercase

def test_order():
    api = CoinSwitchAPI()
    # Validate keys
    try:
        validation = api.validate_keys()
        print(f"API Key Validation: {validation}")
    except Exception as e:
        print(f"API Key Validation Failed: {e}")
        return

    # Get portfolio
    try:
        portfolio = api.get_portfolio()
        print(f"Portfolio: {portfolio}")
    except Exception as e:
        print(f"Failed to get portfolio: {e}")

    # Get all tickers to see available symbols
    try:
        tickers = api.get_all_tickers(EXCHANGE_TEST)
        print(f"All Tickers retrieved, count: {len(tickers)}")
        # Check if ETH/INR is in tickers
        eth_inr = next((t for t in tickers if t.get('symbol') == 'ETH/INR'), None)
        if eth_inr:
            print(f"ETH/INR Ticker: {eth_inr}")
        else:
            print("ETH/INR not found in tickers")
            # Print first few tickers
            for t in tickers[:5]:
                print(f"Sample Ticker: {t}")
    except Exception as e:
        print(f"Failed to get tickers: {e}")

    # Place a test futures order as per example
    symbol = 'dogeusdt'
    side = 'BUY'
    order_type = 'LIMIT'
    price = 0.28
    quantity = 22
    exchange = 'EXCHANGE_2'

    try:
        order = api.place_order(side, symbol, order_type, price, quantity, EXCHANGE)
        print(f"Test Order Placed: {order}")
    except Exception as e:
        print(f"Failed to place order: {e}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
if __name__ == '__main__':
    test_order()