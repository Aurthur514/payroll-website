import time
import logging
from api_wrapper import CoinSwitchAPI
from data_fetcher import DataFetcher
from strategy_manager import StrategyManager
from decision_maker import DecisionMaker
from self_updater import SelfUpdater
import config
from config import UPDATE_INTERVAL, TRAINING_DATA_DAYS, LOG_FILE, LIVE_TRADING

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting trading bot")

    if LIVE_TRADING:
        print("=" * 50)
        print("WARNING: LIVE TRADING MODE ENABLED")
        print("REAL MONEY WILL BE USED FOR TRADES")
        print("=" * 50)
        print("Press Ctrl+C within 10 seconds to cancel...")
        import time
        time.sleep(10)
        print("Starting live trading...")

    data_fetcher = DataFetcher()

    # Set SYMBOLS dynamically
    try:
        all_symbols = data_fetcher.get_all_symbols()
        if not all_symbols:
            print("Warning: No symbols loaded, using defaults")
            config.SYMBOLS = ['ETH/INR', 'BTC/INR', 'ADA/INR', 'SOL/INR']
        else:
            config.SYMBOLS = all_symbols
            logging.info(f"Loaded {len(all_symbols)} symbols")
    except Exception as e:
        logging.error(f"Failed to fetch symbols: {e}")
        config.SYMBOLS = ['ETH/INR', 'BTC/INR', 'ADA/INR', 'SOL/INR']

    api = CoinSwitchAPI()
    # Validate API keys
    try:
        validation = api.validate_keys()
        print(f"API Key Validation: {validation}")
        logging.info(f"API Key Validation: {validation}")
    except Exception as e:
        print(f"API Key Validation Failed: {e}")
        logging.error(f"API Key Validation Failed: {e}")
        return
    strategy_manager = StrategyManager()
    updater = SelfUpdater(strategy_manager, data_fetcher)
    decision_maker = DecisionMaker(api, data_fetcher, strategy_manager, updater, 'ETH/INR')  # Default symbol

    # Initial training on default symbol
    try:
        df = data_fetcher.get_candles('ETH/INR', resolution='1h', days=TRAINING_DATA_DAYS)
        strategy_manager.strategies['ml_strategy'].train_model(df)
        logging.info("Initial model training completed")
    except Exception as e:
        logging.error(f"Initial training failed: {e}")
        print(f"Training failed: {e}")
        return

    print("Bot started. Press Ctrl+C to stop.")

    while True:
        try:
            # Auto-switch strategy based on market conditions
            if not decision_maker.position:  # Only switch when not in position
                df_btc = data_fetcher.get_candles('BTC/INR', resolution='1h', days=1)
                if df_btc is not None and len(df_btc) >= 50:
                    strategy_manager.auto_switch_strategy(df_btc)

            # Check BTC trend
            btc_trend = data_fetcher.get_btc_trend()
            if btc_trend == 'falling':
                logging.info("BTC is falling, skipping trades")
                time.sleep(UPDATE_INTERVAL)
                continue

            if not decision_maker.position:
                # Get high volume symbols
                high_vol_symbols = data_fetcher.get_high_volume_symbols(min_volume=20000000)  # 20M
                available_symbols = [s for s in config.SYMBOLS if s in high_vol_symbols]
                if not available_symbols:
                    logging.info("No high volume symbols available")
                    time.sleep(UPDATE_INTERVAL)
                    continue

                # Scan for buy opportunities
                best_symbol = None
                for symbol in available_symbols:
                    df = data_fetcher.get_candles(symbol, resolution='1h', days=1)
                    if df is None or len(df) < 10:
                        continue
                    signal = strategy_manager.get_signal(df, symbol)
                    if signal == 1:
                        best_symbol = symbol
                        break  # Take the first buy signal
                if best_symbol:
                    decision_maker.symbol = best_symbol
                    decision = 'buy'
                    decision_maker.execute_decision(decision)
            else:
                # Check for close on current position
                df = data_fetcher.get_candles(decision_maker.symbol, resolution='1h', days=1)
                if df is not None and len(df) >= 10:
                    decision = decision_maker.decide(df)
                    decision_maker.execute_decision(decision)
            updater.update_if_needed()
            time.sleep(UPDATE_INTERVAL)
        except KeyboardInterrupt:
            logging.info("Bot stopped by user")
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()