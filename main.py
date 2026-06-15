import json
import logging
import os
import time
from datetime import datetime
from core.execution_engine import MT5ExecutionEngine
from core.signal_generator import MLSignalGenerator

os.makedirs('logs', exist_ok=True)
file_handler = logging.FileHandler(f"logs/bot_activity_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8')
stream_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)

def load_credentials(filepath: str = 'config/keys.json') -> dict:
    with open(filepath, 'r') as file:
        return json.load(file)

def calculate_position_size(capital: float, risk_pct: float, sl_distance: float) -> float:
    if sl_distance <= 0:
        return 0.0
    cash_at_risk = capital * (risk_pct / 100.0)
    # Asumsi: Akun standar XAUUSD (1 Lot = 100 Oz). 
    # Sesuaikan divisor jika Anda menggunakan akun Cent!
    return (cash_at_risk / sl_distance) / 100 

def market_scan_cycle():
    """Satu siklus penuh pemindaian dan eksekusi."""
    creds = load_credentials()
    target_symbol = "XAUUSDm"
    engine = None
    
    try:
        engine = MT5ExecutionEngine(creds['account'], creds['password'], creds['server'])
        capital = engine.fetch_account_balance()
        
        if capital <= 0:
            logger.warning("[SYSTEM] Margin tidak mencukupi.")
            return

        detector = MLSignalGenerator(symbol=target_symbol)
        raw_data = detector.fetch_market_data(num_candles=200)
        
        if raw_data.empty:
            return
            
        processed_data = detector.extract_features(raw_data)
        signal_packet = detector.generate_signal(processed_data)
        
        action = signal_packet["action"]
        current_price = signal_packet["current_price"]
        sl_distance = signal_packet["sl_distance"]
        
        if action in ["BUY", "SELL"]:
            logger.info(f"❖ [TRIGGER] Menginisiasi protokol eksekusi untuk {action}")
            stop_loss_price = current_price - sl_distance if action == "BUY" else current_price + sl_distance
            
            # Hitung lot (Risiko 1%)
            safe_lot = calculate_position_size(capital, 1.0, sl_distance)
            
            # EKSEKUSI RIIL KE EXNESS
            engine.send_order_to_broker(target_symbol, action, safe_lot, stop_loss_price)
            
    except Exception as e:
        logger.error(f"[FATAL] Siklus terputus: {e}")
    finally:
        if engine:
            engine.shutdown()

def main():
    logger.info("=== QUANT BOT AUTOPILOT ACTIVATED ===")
    logger.info("Bot akan memindai pasar setiap 15 menit. Tekan Ctrl+C untuk mematikan.")
    
    # Interval dalam hitungan detik (15 Menit = 900 Detik)
    SCAN_INTERVAL = 900 
    
    try:
        while True:
            logger.info(f"\n--- Memulai Siklus Pemindaian: {datetime.now().strftime('%H:%M:%S')} ---")
            market_scan_cycle()
            
            logger.info(f"[SLEEP] Menunggu {SCAN_INTERVAL / 60} menit untuk siklus berikutnya...\n")
            time.sleep(SCAN_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("\n=== AUTOPILOT DIMATIKAN OLEH USER (Ctrl+C) ===")

if __name__ == "__main__":
    main()