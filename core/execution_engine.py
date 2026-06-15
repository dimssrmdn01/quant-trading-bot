import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)

class MT5ExecutionEngine:
    """
    Modul eksekusi algoritmik khusus untuk terminal MetaTrader 5 (Exness dll).
    """
    def __init__(self, account: int, password: str, server: str):
        # 1. Menyalakan Terminal MT5
        if not mt5.initialize():
            logger.error(f"[FATAL] Inisialisasi MT5 gagal. Kode eror: {mt5.last_error()}")
            raise Exception("MT5 Initialization Failed")
            
        # 2. Autentikasi ke Server Broker
        authorized = mt5.login(login=account, password=password, server=server)
        if not authorized:
            logger.error(f"[FATAL] Autentikasi gagal ke {server}. Eror: {mt5.last_error()}")
            mt5.shutdown()
            raise Exception("MT5 Login Failed")
            
        logger.info(f"❖ Engine terhubung ke MT5 ({server}) | Akun: {account}")

    def fetch_account_balance(self) -> float:
        """Menarik data Free Margin (Saldo yang bisa digunakan untuk trading)."""
        account_info = mt5.account_info()
        if account_info is None:
            logger.error(f"[ERROR] Gagal menarik data akun. Eror: {mt5.last_error()}")
            return 0.0
            
        return float(account_info.margin_free)

    def shutdown(self):
        """Memutus koneksi dengan aman saat bot dimatikan."""
        mt5.shutdown()
        logger.info("❖ Koneksi MT5 diputus dengan aman.")

def send_order_to_broker(self, symbol: str, action: str, volume: float, stop_loss: float):
        """Mengirim perintah eksekusi riil (Market Order) ke server MT5 beserta Stop Loss."""
        # 1. Pastikan instrumen aktif di terminal
        mt5.symbol_select(symbol, True)
        
        # 2. Tarik harga Ask/Bid detik ini
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"[FATAL] Gagal menarik harga bid/ask untuk {symbol}.")
            return None

        # 3. Konfigurasi Arah Order
        if action == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid

        # Pembulatan lot standar ke 2 desimal (0.01)
        safe_volume = round(volume, 2)
        if safe_volume <= 0:
            logger.warning("[WARNING] Kalkulasi Lot terlalu kecil (<0.01). Order dibatalkan.")
            return None

        # 4. Rakit Tiket Order Standar Institusi
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(safe_volume),
            "type": order_type,
            "price": price,
            "sl": float(stop_loss),
            "deviation": 10, # Toleransi slippage 10 poin
            "magic": 101010, # ID unik untuk melacak order dari bot ini
            "comment": "Lasso_AI_Quant",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC, # Immediate or Cancel
        }
        
        logger.info(f"❖ [EXECUTION] Menembakkan Market {action} | Lot: {safe_volume} | Harga: {price} | SL: {stop_loss:.2f}")
        
        # 5. Tembak ke Server Exness!
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"■ [REJECTED] Order ditolak. Kode eror: {result.retcode} - {result.comment}")
        else:
            logger.info(f"❖ [SUCCESS] Transaksi Tereksekusi! Nomor Tiket: {result.order}")
            
        return result