from config import RISK_PER_TRADE, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, EXCHANGE, LEVERAGE, LIVE_TRADING, SYMBOL

class DecisionMaker:
    def __init__(self, api, data_fetcher, strategy_manager, updater, symbol):
        self.api = api
        self.data_fetcher = data_fetcher
        self.strategy_manager = strategy_manager
        self.updater = updater
        self.symbol = symbol
        self.position = None  # {'side': 'buy', 'entry_price': , 'quantity': , 'order_id': }
        self.portfolio = None

    def update_portfolio(self):
        try:
            self.portfolio = self.api.get_portfolio()
        except:
            self.portfolio = {'data': {'INR': {'main_balance': '1000000'}, 'BTC': {'main_balance': '0'}}}

    def get_balance(self, currency='INR'):
        self.update_portfolio()
        if 'data' in self.portfolio and isinstance(self.portfolio['data'], dict):
            if currency in self.portfolio['data']:
                return float(self.portfolio['data'][currency]['main_balance'])
        return 0.0

    def decide(self, df):
        signal = self.strategy_manager.get_signal(df, self.symbol)
        current_price = self.data_fetcher.get_current_price(self.symbol)
        
        if current_price is None:
            return 'hold'  # Can't make decisions without price data

        # Check existing position for stop loss/take profit
        if self.position:
            entry_price = self.position['entry_price']
            if self.position['side'] == 'buy':
                stop_loss_price = entry_price * (1 - STOP_LOSS_PERCENT)
                take_profit_price = entry_price * (1 + TAKE_PROFIT_PERCENT)
                if current_price <= stop_loss_price or current_price >= take_profit_price:
                    return 'close_buy'  # Sell to close long position
            elif self.position['side'] == 'sell':
                stop_loss_price = entry_price * (1 + STOP_LOSS_PERCENT)
                take_profit_price = entry_price * (1 - TAKE_PROFIT_PERCENT)
                if current_price >= stop_loss_price or current_price <= take_profit_price:
                    return 'close_sell'  # Buy to close short position

        # New position based on signal
        if signal == 1 and not self.position:  # Buy signal
            return 'buy'
        elif signal == -1 and not self.position:  # Sell signal
            return 'sell'

        return 'hold'

    def execute_decision(self, decision):
        current_price = self.data_fetcher.get_current_price(self.symbol)
        if current_price is None:
            print(f"Error: Could not get current price for {self.symbol}")
            return
            
        balance = self.get_balance('INR')

        # Safety checks for live trading
        if LIVE_TRADING:
            print(f"WARNING: LIVE TRADING MODE - About to execute {decision.upper()} order")
            print(f"Symbol: {self.symbol}, Price: {current_price}, Balance: {balance}")

            # Minimum balance check
            if balance < 100:  # Minimum 100 INR
                print("ERROR: Insufficient balance for live trading")
                return

            # Confirm the trade
            import time
            print("Waiting 3 seconds for confirmation...")
            time.sleep(3)

        trade_info = self.data_fetcher.get_trade_info(self.symbol)
        min_quantity = float(trade_info.get('min_quantity', 0.00001))
        max_quantity = float(trade_info.get('max_quantity', float('inf')))

        if decision == 'buy':
            quantity = (balance * RISK_PER_TRADE * LEVERAGE) / current_price
            quantity = max(min_quantity, min(max_quantity, quantity))
            if quantity > 0:
                if LIVE_TRADING:
                    print(f"EXECUTING LIVE BUY ORDER: {quantity} {SYMBOL} at {current_price} INR")
                    order = self.api.place_order('buy', SYMBOL, 'limit', current_price, quantity, EXCHANGE)
                    if 'order_id' in order:
                        self.position = {
                            'side': 'buy',
                            'entry_price': current_price,
                            'quantity': quantity,
                            'order_id': order['order_id']
                        }
                        print(f"LIVE BUY ORDER PLACED: {order['order_id']}")
                    else:
                        print(f"FAILED TO PLACE LIVE BUY ORDER: {order}")
                else:
                    print(f"Simulation: Would place buy order for {quantity} {SYMBOL} at {current_price}")
                    self.position = {
                        'side': 'buy',
                        'entry_price': current_price,
                        'quantity': quantity,
                        'order_id': 'simulated'
                    }

        elif decision in ['close_buy', 'sell']:
            if self.position and self.position['side'] == 'buy':
                quantity = min(max_quantity, self.position['quantity'])  # Ensure within limits
                if LIVE_TRADING:
                    print(f"EXECUTING LIVE SELL ORDER: {quantity} {SYMBOL} at {current_price} INR")
                    order = self.api.place_order('sell', SYMBOL, 'limit', current_price, quantity, EXCHANGE)
                    if 'order_id' in order:
                        print(f"LIVE SELL ORDER PLACED: {order['order_id']}")
                        # Record trade
                        self.updater.record_trade('buy', self.position['entry_price'], current_price, quantity)
                        self.position = None
                    else:
                        print(f"FAILED TO PLACE LIVE SELL ORDER: {order}")
                else:
                    print(f"Simulation: Would place sell order to close position for {quantity} {SYMBOL} at {current_price}")
                    self.updater.record_trade('buy', self.position['entry_price'], current_price, quantity)
                    self.position = None

        elif decision == 'close_sell':
            if self.position and self.position['side'] == 'sell':
                quantity = min(max_quantity, self.position['quantity'])
                if LIVE_TRADING:
                    order = self.api.place_order('buy', SYMBOL, 'limit', current_price, quantity, EXCHANGE)
                    if 'order_id' in order:
                        print(f"Placed buy order to close position: {order}")
                        # Record trade
                        self.updater.record_trade('sell', self.position['entry_price'], current_price, quantity)
                        self.position = None
                    else:
                        print(f"Failed to place buy order: {order}")
                else:
                    print(f"Simulation: Would place buy order to close position for {quantity} {SYMBOL} at {current_price}")
                    self.updater.record_trade('sell', self.position['entry_price'], current_price, quantity)
                    self.position = None

        # For short selling, if supported
        elif decision == 'sell' and not self.position:
            # Assuming short selling is allowed
            quantity = (balance * RISK_PER_TRADE * LEVERAGE) / current_price
            quantity = max(min_quantity, min(max_quantity, quantity))
            if LIVE_TRADING:
                print(f"EXECUTING LIVE SHORT SELL ORDER: {quantity} {SYMBOL} at {current_price} INR")
                order = self.api.place_order('sell', SYMBOL, 'limit', current_price, quantity, EXCHANGE)
                if 'order_id' in order:
                    self.position = {
                        'side': 'sell',
                        'entry_price': current_price,
                        'quantity': quantity,
                        'order_id': order['order_id']
                    }
                    print(f"LIVE SHORT SELL ORDER PLACED: {order['order_id']}")
                else:
                    print(f"FAILED TO PLACE LIVE SHORT SELL ORDER: {order}")
            else:
                print(f"Simulation: Would place sell order for {quantity} {SYMBOL} at {current_price}")
                self.position = {
                    'side': 'sell',
                    'entry_price': current_price,
                    'quantity': quantity,
                    'order_id': 'simulated'
                }