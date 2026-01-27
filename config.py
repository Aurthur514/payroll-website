# CoinSwitch API Configuration
# Replace with your actual keys from CoinSwitch PRO profile
import os
API_KEY = os.getenv('COINSWITCH_API_KEY')
API_SECRET = os.getenv('COINSWITCH_API_SECRET')  # Ed25519 private key in hex or bytes

if not API_KEY or not API_SECRET:
    raise ValueError("COINSWITCH_API_KEY and COINSWITCH_API_SECRET environment variables must be set")

BASE_URL = 'https://coinswitch.co'

# Trading mode
LIVE_TRADING = False  # Set to True for real trading, False for simulation

# Default settings
EXCHANGE = 'coinswitchx'  # Available: coinswitchx, wazirx, c2c1, c2c2
# SYMBOLS = ['ETH/INR', 'BTC/INR', 'ADA/INR', 'SOL/INR']  # List of trading pairs to monitor - now auto fetched
SYMBOL = 'ETH/INR'  # Default symbol, used for single operations if needed

# Risk management
RISK_PER_TRADE = 0.05  # Fraction of portfolio per trade (0.01 = 1%)
STOP_LOSS_PERCENT = 0.05  # 5% stop loss
TAKE_PROFIT_PERCENT = 0.10  # 10% take profit
LEVERAGE = 10  # Leverage multiplier (1 for spot trading)

# ML and data settings
MODEL_PATH = 'trading_model.pkl'
DATA_WINDOW = 120  # Number of minutes of historical data for pattern recognition
UPDATE_INTERVAL = 60  # Seconds between checks
TRAINING_DATA_DAYS = 30  # Days of historical data for initial training

# Logging
LOG_FILE = 'trading_bot.log'

# Auto get all available INR symbols - will be set in main
SYMBOLS = []