import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
from config import MODEL_PATH
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class StrategyManager:
    def __init__(self):
        self.strategies = {
            'ml_strategy': MLStrategy(),
            'mean_reversion': MeanReversionStrategy(),
            'trend_following': TrendFollowingStrategy(),
            'rsi_divergence': RSIDivergenceStrategy(),
            'bollinger_bands': BollingerBandStrategy(),
            'sma_crossover': SMACrossoverStrategy()  # Consistent strategy
        }
        self.active_strategy = 'ml_strategy'  # Default
        self.fail_safes = FailSafes()

    def set_active_strategy(self, strategy_name):
        if strategy_name in self.strategies:
            old_strategy = self.active_strategy
            self.active_strategy = strategy_name
            if old_strategy != strategy_name:
                print(f"Switched strategy from {old_strategy} to {strategy_name}")
        else:
            print(f"Strategy {strategy_name} not found")

    def get_signal(self, df, symbol):
        # Check fail safes first
        if self.fail_safes.should_stop_trading():
            return 0  # No signal

        # Get signal from active strategy
        strategy = self.strategies[self.active_strategy]
        signal = strategy.get_signal(df)

        # Apply additional filters
        if self.fail_safes.is_high_volatility(df):
            signal = 0  # No trading in high volatility

        return signal

    def update_after_trade(self, trade_result):
        self.fail_safes.update_trade_history(trade_result)

    def auto_switch_strategy(self, df):
        """Automatically switch to the most appropriate strategy based on market conditions"""
        if len(df) < 50:
            return

        # Calculate market indicators
        volatility = df['close'].pct_change().std() * np.sqrt(24)  # Daily volatility
        trend_strength = abs(talib.LINEARREG_SLOPE(df['close'], timeperiod=20).iloc[-1])

        # High volatility + weak trend -> Mean Reversion
        if volatility > 0.05 and trend_strength < 0.001:
            self.set_active_strategy('mean_reversion')
        # High volatility + strong trend -> Trend Following
        elif volatility > 0.05 and trend_strength > 0.002:
            self.set_active_strategy('trend_following')
        # Low volatility -> SMA Crossover (consistent)
        elif volatility < 0.02:
            self.set_active_strategy('sma_crossover')
        # Default to ML strategy
        else:
            self.set_active_strategy('ml_strategy')

class MLStrategy:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.load_model()

    def calculate_indicators(self, df):
        df = df.copy()
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        df['macd'], df['macdsignal'], df['macdhist'] = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        df['upperband'], df['middleband'], df['lowerband'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
        df['ema_12'] = talib.EMA(df['close'], timeperiod=12)
        return df

    def prepare_features(self, df, predict=False):
        df = self.calculate_indicators(df)
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()

        for lag in range(1, 6):
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'rsi_lag_{lag}'] = df['rsi'].shift(lag)
            df[f'macd_lag_{lag}'] = df['macd'].shift(lag)

        df = df.replace([np.inf, -np.inf], np.nan)

        if not predict:
            df['future_close'] = df['close'].shift(-1)
            df['target'] = np.where(df['future_close'] > df['close'] * 1.001, 1,
                                   np.where(df['future_close'] < df['close'] * 0.999, -1, 0))
            df.dropna(inplace=True)
            features = [col for col in df.columns if col not in ['future_close', 'target']]
            return df[features], df['target']
        else:
            df.dropna(inplace=True)
            features = [col for col in df.columns if 'target' not in col and 'future' not in col]
            return df[features]

    def train_model(self, df):
        X, y = self.prepare_features(df)
        if len(X) < 100:
            return
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        self.model.fit(X_train, y_train)
        pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, pred)
        print(f'ML Model trained with accuracy: {acc:.2f}')
        self.save_model()

    def get_signal(self, df):
        if len(df) < 30:
            return 0
        X = self.prepare_features(df, predict=True)
        if len(X) == 0:
            return 0
        pred = self.model.predict(X.iloc[-1:].values)
        return pred[0]

    def save_model(self):
        joblib.dump(self.model, MODEL_PATH)

    def load_model(self):
        try:
            self.model = joblib.load(MODEL_PATH)
        except FileNotFoundError:
            pass

    def get_performance(self):
        return self.performance

class MeanReversionStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.lookback = 20

    def get_signal(self, df):
        if len(df) < self.lookback:
            return 0

        # Calculate z-score
        mean = df['close'].rolling(self.lookback).mean().iloc[-1]
        std = df['close'].rolling(self.lookback).std().iloc[-1]
        current_price = df['close'].iloc[-1]

        if std > 0:
            z_score = (current_price - mean) / std

            # Buy when price is 2 std below mean, sell when 2 std above
            if z_score < -2:
                return 1  # Buy signal
            elif z_score > 2:
                return -1  # Sell signal

        return 0

    def get_performance(self):
        return self.performance

class TrendFollowingStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}

    def get_signal(self, df):
        if len(df) < 50:
            return 0

        # Use multiple EMAs for trend confirmation
        ema_20 = talib.EMA(df['close'], timeperiod=20).iloc[-1]
        ema_50 = talib.EMA(df['close'], timeperiod=50).iloc[-1]
        current_price = df['close'].iloc[-1]

        # Strong uptrend: price > EMA20 > EMA50
        if current_price > ema_20 > ema_50:
            return 1
        # Strong downtrend: price < EMA20 < EMA50
        elif current_price < ema_20 < ema_50:
            return -1

        return 0

    def get_performance(self):
        return self.performance

class RSIDivergenceStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}

    def get_signal(self, df):
        if len(df) < 30:
            return 0

        rsi = talib.RSI(df['close'], timeperiod=14)
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]

        # Oversold: RSI < 30, improving
        if current_rsi < 30 and current_rsi > prev_rsi:
            return 1
        # Overbought: RSI > 70, declining
        elif current_rsi > 70 and current_rsi < prev_rsi:
            return -1

        return 0

    def get_performance(self):
        return self.performance

class SMACrossoverStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.fast_period = 10
        self.slow_period = 20

    def get_signal(self, df):
        if len(df) < self.slow_period + 5:
            return 0

        # Calculate SMAs
        fast_sma = talib.SMA(df['close'], timeperiod=self.fast_period)
        slow_sma = talib.SMA(df['close'], timeperiod=self.slow_period)

        # Check for crossover in recent periods
        current_fast = fast_sma.iloc[-1]
        current_slow = slow_sma.iloc[-1]
        prev_fast = fast_sma.iloc[-2]
        prev_slow = slow_sma.iloc[-2]

        # Bullish crossover: fast SMA crosses above slow SMA
        if prev_fast <= prev_slow and current_fast > current_slow:
            return 1
        # Bearish crossover: fast SMA crosses below slow SMA
        elif prev_fast >= prev_slow and current_fast < current_slow:
            return -1

        return 0

    def get_performance(self):
        return self.performance

class FailSafes:
    def __init__(self):
        self.daily_loss_limit = 0.05  # 5% daily loss limit
        self.max_drawdown_limit = 0.10  # 10% max drawdown
        self.max_consecutive_losses = 5
        self.emergency_stop = False

        # Tracking variables
        self.daily_start_balance = 1000000  # Should be updated from actual balance
        self.peak_balance = 1000000
        self.current_balance = 1000000
        self.consecutive_losses = 0
        self.trade_history = []

        # Circuit breaker: stop if volatility too high
        self.volatility_threshold = 0.05  # 5% price change in last hour

    def update_trade_history(self, trade_result):
        self.trade_history.append(trade_result)
        pnl = trade_result.get('pnl', 0)
        self.current_balance += pnl

        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        self.peak_balance = max(self.peak_balance, self.current_balance)

    def should_stop_trading(self):
        if self.emergency_stop:
            return True

        # Check daily loss limit
        daily_loss = (self.daily_start_balance - self.current_balance) / self.daily_start_balance
        if daily_loss > self.daily_loss_limit:
            print(f"Daily loss limit reached: {daily_loss:.2%}")
            return True

        # Check max drawdown
        drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        if drawdown > self.max_drawdown_limit:
            print(f"Max drawdown limit reached: {drawdown:.2%}")
            return True

        # Check consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            print(f"Max consecutive losses reached: {self.consecutive_losses}")
            return True

        return False

    def is_high_volatility(self, df):
        if len(df) < 2:
            return False

        recent_prices = df['close'].tail(10)  # Last 10 periods
        price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]

        return abs(price_change) > self.volatility_threshold

    def emergency_stop_trading(self):
        self.emergency_stop = True
        print("EMERGENCY STOP ACTIVATED")

    def reset_daily_limits(self):
        self.daily_start_balance = self.current_balance
        self.consecutive_losses = 0

    def get_status(self):
        return {
            'emergency_stop': self.emergency_stop,
            'current_balance': self.current_balance,
            'daily_loss': (self.daily_start_balance - self.current_balance) / self.daily_start_balance,
            'drawdown': (self.peak_balance - self.current_balance) / self.peak_balance,
            'consecutive_losses': self.consecutive_losses
        }
<parameter name="filePath">f:\bharathan\trade\strategy_manager.py
