class SelfUpdater:
    def __init__(self, strategy_manager, data_fetcher):
        self.strategy_manager = strategy_manager
        self.data_fetcher = data_fetcher
        self.trades = []  # List of {'profit': float, 'decision': str, 'entry_price': float, 'exit_price': float}

    def record_trade(self, decision, entry_price, exit_price, quantity):
        if decision == 'buy':
            profit = (exit_price - entry_price) * quantity
        elif decision == 'sell':
            profit = (entry_price - exit_price) * quantity
        else:
            profit = 0
        trade_result = {
            'profit': profit,
            'pnl': profit,
            'decision': decision,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity
        }
        self.trades.append(trade_result)
        print(f"Recorded trade: {decision}, Profit: {profit}")

        # Update fail safes
        self.strategy_manager.fail_safes.update_trade_history(trade_result)

    def evaluate_performance(self):
        if not self.trades:
            return 0, 0
        total_profit = sum(t['profit'] for t in self.trades)
        win_rate = sum(1 for t in self.trades if t['profit'] > 0) / len(self.trades)
        return total_profit, win_rate

    def update_if_needed(self):
        total_profit, win_rate = self.evaluate_performance()
        print(f"Total Profit: {total_profit}, Win Rate: {win_rate:.2f}")

        # Update if win rate below 50% or negative profit
        if win_rate < 0.5 or total_profit < 0:
            print("Performance poor, updating model...")
            df = self.data_fetcher.get_candles('ETH/INR', resolution='1h', days=30)
            self.strategy_manager.strategies['ml_strategy'].train_model(df)
            print("Model updated.")
        else:
            print("Performance acceptable, no update needed.")