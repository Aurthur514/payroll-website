import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import talib
import joblib
from config import MODEL_PATH

class PatternRecognizer:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.load_model()

    def calculate_indicators(self, df):
        # Calculate technical indicators
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

        # Lag features
        for lag in range(1, 6):
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'rsi_lag_{lag}'] = df['rsi'].shift(lag)
            df[f'macd_lag_{lag}'] = df['macd'].shift(lag)

        # Replace inf with nan
        df = df.replace([np.inf, -np.inf], np.nan)

        if not predict:
            # Target: future price direction (1: buy/up, -1: sell/down, 0: hold)
            df['future_close'] = df['close'].shift(-1)
            df['target'] = np.where(df['future_close'] > df['close'] * 1.001, 1,  # 0.1% up
                                   np.where(df['future_close'] < df['close'] * 0.999, -1, 0))  # 0.1% down
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
            print("Not enough data for training")
            return
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        self.model.fit(X_train, y_train)
        pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, pred)
        print(f'Model trained with accuracy: {acc:.2f}')
        self.save_model()

    def predict_signal(self, df):
        if len(df) < 30:  # Need enough data for indicators
            return 0
        X = self.prepare_features(df, predict=True)
        if len(X) == 0:
            return 0
        pred = self.model.predict(X.iloc[-1:].values)
        return pred[0]

    def update_model(self, new_df):
        # Retrain with new data
        self.train_model(new_df)

    def save_model(self):
        joblib.dump(self.model, MODEL_PATH)

    def load_model(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            print("Model loaded successfully")
        except FileNotFoundError:
            print("No saved model found, will train new one")