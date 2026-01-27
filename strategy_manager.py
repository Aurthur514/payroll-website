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
            'sma_crossover': SMACrossoverStrategy(),
            'scalping': ScalpingStrategy(),
            'momentum': MomentumStrategy(),
            'breakout': BreakoutStrategy(),
            'volume_spike': VolumeSpikeStrategy(),
            'support_resistance': SupportResistanceStrategy(),
            'fibonacci_retracement': FibonacciRetracementStrategy(),
            'stochastic_oscillator': StochasticOscillatorStrategy(),
            'volume_price_analysis': VolumePriceAnalysisStrategy(),
            'adaptive_strategy': AdaptiveStrategy()
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
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(20).mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # RSI for momentum
        rsi = talib.RSI(df['close'], timeperiod=14).iloc[-1]

        # Choose strategy based on conditions
        if volatility > 0.05 and trend_strength < 0.001:
            self.set_active_strategy('mean_reversion')  # High vol, weak trend
        elif volatility > 0.05 and trend_strength > 0.002:
            self.set_active_strategy('momentum')  # High vol, strong trend
        elif volatility < 0.02:
            self.set_active_strategy('sma_crossover')  # Low vol, use consistent strategy
        elif volume_ratio > 2.0:
            self.set_active_strategy('volume_spike')  # Volume spike
        elif rsi < 30 or rsi > 70:
            self.set_active_strategy('rsi_divergence')  # Overbought/oversold
        elif len(df) > 100 and trend_strength > 0.001:
            self.set_active_strategy('breakout')  # Potential breakouts
        elif volatility > 0.03:
            self.set_active_strategy('scalping')  # High frequency in volatile markets
        else:
            self.set_active_strategy('support_resistance')  # Default to S/R strategy

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

class BollingerBandStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}

    def get_signal(self, df):
        if len(df) < 25:
            return 0

        upper, middle, lower = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
        current_price = df['close'].iloc[-1]

        # Buy when price touches lower band
        if current_price <= lower.iloc[-1] * 1.001:  # Within 0.1%
            return 1
        # Sell when price touches upper band
        elif current_price >= upper.iloc[-1] * 0.999:  # Within 0.1%
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

class ScalpingStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.lookback = 5

    def get_signal(self, df):
        if len(df) < self.lookback:
            return 0

        # Look for quick momentum changes
        recent_prices = df['close'].tail(self.lookback)
        recent_volumes = df['volume'].tail(self.lookback)

        # Calculate price momentum
        price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
        volume_avg = recent_volumes.mean()
        current_volume = recent_volumes.iloc[-1]

        # Scalp signals: small price movements with volume confirmation
        if price_change > 0.002 and current_volume > volume_avg * 1.2:  # 0.2% up with volume
            return 1
        elif price_change < -0.002 and current_volume > volume_avg * 1.2:  # 0.2% down with volume
            return -1

        return 0

    def get_performance(self):
        return self.performance

class MomentumStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}

    def get_signal(self, df):
        if len(df) < 20:
            return 0

        # Calculate momentum indicators
        roc = talib.ROC(df['close'], timeperiod=10)  # Rate of change
        macd, macdsignal, macdhist = talib.MACD(df['close'])

        current_roc = roc.iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = macdsignal.iloc[-1]

        # Strong momentum signals
        if current_roc > 2 and current_macd > current_signal:
            return 1  # Strong upward momentum
        elif current_roc < -2 and current_macd < current_signal:
            return -1  # Strong downward momentum

        return 0

    def get_performance(self):
        return self.performance

class BreakoutStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.lookback = 20

    def get_signal(self, df):
        if len(df) < self.lookback + 5:
            return 0

        # Calculate recent high/low
        recent_high = df['high'].tail(self.lookback).max()
        recent_low = df['low'].tail(self.lookback).min()
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]

        # Volume confirmation
        avg_volume = df['volume'].tail(self.lookback).mean()
        current_volume = df['volume'].iloc[-1]

        # Breakout signals
        if current_price > recent_high * 0.995 and current_volume > avg_volume and prev_price <= recent_high:
            return 1  # Break above resistance
        elif current_price < recent_low * 1.005 and current_volume > avg_volume and prev_price >= recent_low:
            return -1  # Break below support

        return 0

    def get_performance(self):
        return self.performance

class VolumeSpikeStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.lookback = 20

    def get_signal(self, df):
        if len(df) < self.lookback:
            return 0

        # Calculate volume moving average
        volume_ma = df['volume'].tail(self.lookback).mean()
        current_volume = df['volume'].iloc[-1]
        prev_volume = df['volume'].iloc[-2]

        # Price action
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]

        # Volume spike with price confirmation
        volume_ratio = current_volume / volume_ma if volume_ma > 0 else 0

        if volume_ratio > 2.0:  # 2x average volume
            if current_price > prev_price:
                return 1  # High volume up move
            elif current_price < prev_price:
                return -1  # High volume down move

        return 0

    def get_performance(self):
        return self.performance

class SupportResistanceStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.lookback = 50

    def get_signal(self, df):
        if len(df) < self.lookback:
            return 0

        # Find support and resistance levels
        recent_data = df.tail(self.lookback)
        pivot_high = recent_data['high'].max()
        pivot_low = recent_data['low'].min()

        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]

        # Calculate distance from levels
        resistance_distance = abs(current_price - pivot_high) / pivot_high
        support_distance = abs(current_price - pivot_low) / pivot_low

        # Bounce signals near key levels
        if resistance_distance < 0.01 and current_price < prev_price:
            return -1  # Reject resistance, sell
        elif support_distance < 0.01 and current_price > prev_price:
            return 1  # Bounce off support, buy

        return 0

    def get_performance(self):
        return self.performance

class FibonacciRetracementStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.lookback_period = 50
        self.fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]

    def get_signal(self, df):
        if len(df) < self.lookback_period:
            return 0

        # Find recent high and low
        recent_high = df['high'].tail(self.lookback_period).max()
        recent_low = df['low'].tail(self.lookback_period).min()
        current_price = df['close'].iloc[-1]

        # Calculate Fibonacci levels
        fib_range = recent_high - recent_low
        fib_levels = [recent_high - level * fib_range for level in self.fib_levels]

        # Check if price is near support/resistance levels
        for level in fib_levels:
            if abs(current_price - level) / current_price < 0.005:  # Within 0.5%
                # Check trend direction
                sma_20 = talib.SMA(df['close'], timeperiod=20).iloc[-1]
                if current_price > sma_20 and level > sma_20:
                    return 1  # Buy near support
                elif current_price < sma_20 and level < sma_20:
                    return -1  # Sell near resistance

        return 0

    def get_performance(self):
        return self.performance

class StochasticOscillatorStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.k_period = 14
        self.d_period = 3
        self.overbought = 80
        self.oversold = 20

    def get_signal(self, df):
        if len(df) < self.k_period:
            return 0

        # Calculate Stochastic Oscillator
        slowk, slowd = talib.STOCH(df['high'], df['low'], df['close'],
                                  fastk_period=self.k_period, slowk_period=3,
                                  slowd_period=self.d_period)

        k_current = slowk.iloc[-1]
        d_current = slowd.iloc[-1]
        k_prev = slowk.iloc[-2]
        d_prev = slowd.iloc[-2]

        # Oversold condition - Buy signal
        if k_current < self.oversold and d_current < self.oversold and k_current > k_prev:
            return 1
        # Overbought condition - Sell signal
        elif k_current > self.overbought and d_current > self.overbought and k_current < k_prev:
            return -1

        return 0

    def get_performance(self):
        return self.performance

class VolumePriceAnalysisStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.volume_period = 20
        self.price_period = 10

    def get_signal(self, df):
        if len(df) < self.volume_period:
            return 0

        # Volume analysis
        volume_sma = talib.SMA(df['volume'], timeperiod=self.volume_period)
        current_volume = df['volume'].iloc[-1]
        avg_volume = volume_sma.iloc[-1]

        # Price momentum
        roc = talib.ROC(df['close'], timeperiod=self.price_period).iloc[-1]

        # High volume + positive momentum = Buy
        if current_volume > avg_volume * 1.5 and roc > 2:
            return 1
        # High volume + negative momentum = Sell
        elif current_volume > avg_volume * 1.5 and roc < -2:
            return -1

        return 0

    def get_performance(self):
        return self.performance

class AdaptiveStrategy:
    def __init__(self):
        self.performance = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        self.strategies = {
            'momentum': MomentumStrategy(),
            'mean_reversion': MeanReversionStrategy(),
            'trend_following': TrendFollowingStrategy()
        }
        self.performance_weights = {name: 1.0 for name in self.strategies.keys()}
        self.current_strategy = 'momentum'

    def get_signal(self, df):
        if len(df) < 50:
            return 0

        # Get signals from all strategies
        signals = {}
        for name, strategy in self.strategies.items():
            signals[name] = strategy.get_signal(df)

        # Weight signals by recent performance
        weighted_signal = 0
        total_weight = 0

        for name, signal in signals.items():
            if signal != 0:
                weight = self.performance_weights.get(name, 1.0)
                weighted_signal += signal * weight
                total_weight += weight

        if total_weight > 0:
            final_signal = weighted_signal / total_weight
            return 1 if final_signal > 0.5 else -1 if final_signal < -0.5 else 0

        return 0

    def update_performance(self, strategy_name, profit):
        """Update strategy weights based on performance"""
        if strategy_name in self.performance_weights:
            # Increase weight for profitable strategies, decrease for losses
            adjustment = profit * 0.1
            self.performance_weights[strategy_name] = max(0.1,
                self.performance_weights[strategy_name] + adjustment)

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
