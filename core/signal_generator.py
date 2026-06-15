import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
from sklearn.linear_model import Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

logger = logging.getLogger(__name__)

class MLSignalGenerator:
    """
    Modul Otak Analitik: Melatih model Machine Learning (Lasso) secara dinamis
    menggunakan data candlestick terbaru untuk memprediksi arah pergerakan harga.
    """
    def __init__(self, symbol: str, timeframe=mt5.TIMEFRAME_M15):
        self.symbol = symbol
        self.timeframe = timeframe
        # Kita menggunakan Lasso karena sangat tangguh dalam menekan (shrinkage) 
        # fitur yang tidak relevan di data finansial yang penuh noise.
        self.model = Lasso(alpha=0.01, random_state=42)
        self.scaler = StandardScaler()
        logger.info(f"❖ ML Engine (Lasso Regression) diinisiasi untuk: {self.symbol}")

    def fetch_market_data(self, num_candles: int = 200) -> pd.DataFrame:
        """Menarik data candlestick historis. Kita butuh lebih banyak data (200) untuk training."""
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, num_candles)
        if rates is None:
            logger.error(f"[ERROR] Gagal menarik data harga untuk {self.symbol}.")
            return pd.DataFrame()
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature Engineering: Menciptakan prediktor untuk model ML.
        """
        # Indikator Tren & Momentum
        df['SMA_10'] = df['close'].rolling(window=10).mean()
        df['SMA_30'] = df['close'].rolling(window=30).mean()
        df['ROC_5'] = df['close'].pct_change(periods=5) * 100
        df['ROC_10'] = df['close'].pct_change(periods=10) * 100
        
        # Volatilitas (ATR)
        df['H-L'] = df['high'] - df['low']
        df['H-PC'] = abs(df['high'] - df['close'].shift(1))
        df['L-PC'] = abs(df['low'] - df['close'].shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        # ---------------------------------------------------------
        # VARIABEL TARGET (Y): Prediksi pergerakan harga (Return) di candle berikutnya
        # Jika nilai positif = Harga akan naik. Jika negatif = Harga turun.
        # ---------------------------------------------------------
        df['Target_Return'] = df['close'].shift(-1) - df['close']
        
        # Bersihkan data dari nilai NaN akibat proses kalkulasi
        df.dropna(inplace=True)
        return df

    def generate_signal(self, df: pd.DataFrame) -> dict:
        """
        Melatih model secara on-the-fly dan mengeksekusi prediksi pada candle terakhir.
        """
        if df.empty or len(df) < 50:
            return {"action": "HOLD", "confidence": 0.0, "sl_distance": 0.0, "current_price": 0.0}

        # 1. Pemisahan Fitur (X) dan Target (Y)
        # Kita buang baris paling terakhir untuk training karena Target-nya belum terjadi
        train_data = df.iloc[:-1]
        
        features = ['SMA_10', 'SMA_30', 'ROC_5', 'ROC_10', 'ATR']
        X_train = train_data[features]
        y_train = train_data['Target_Return']

        # 2. Standarisasi Matriks & Proses Training Otomatis
        X_train_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_train_scaled, y_train)

        # 3. Validasi Model (MSE)
        # Kita validasi seberapa bagus model ini membaca pola 200 candle terakhir
        train_predictions = self.model.predict(X_train_scaled)
        mse_score = mean_squared_error(y_train, train_predictions)
        
        # 4. Prediksi Masa Depan (Inference pada candle terkini)
        latest_data = df.iloc[-1:]
        X_latest = latest_data[features]
        X_latest_scaled = self.scaler.transform(X_latest)
        
        predicted_move = self.model.predict(X_latest_scaled)[0]
        current_price = latest_data['close'].values[0]
        current_atr = latest_data['ATR'].values[0]

        # 5. Mesin Logika Eksekusi
        action = "HOLD"
        confidence = 0.0
        
        # Jika MSE terlalu tinggi (model kebingungan karena noise pasar), paksa HOLD
        if mse_score > (current_atr * 1.5):
            logger.warning(f"❖ Model mendeteksi noise tinggi (MSE: {mse_score:.4f}). Sinyal dibatalkan.")
        else:
            # Kalkulasi pseudo-confidence (semakin rendah MSE, semakin tinggi konfidensi)
            confidence = max(50.0, 100.0 - (mse_score * 10)) 
            
            # Treshold prediksi minimum agar tidak menembak pada pergerakan landai
            if predicted_move > (current_atr * 0.1): 
                action = "BUY"
            elif predicted_move < -(current_atr * 0.1):
                action = "SELL"

        sl_distance = current_atr * 1.5 
        
        logger.info(f"❖ [AI TRAINING] Selesai. MSE: {mse_score:.4f} | Prediksi Pergerakan: {predicted_move:.2f} poin")
        logger.info(f"❖ [DECISION] Aksi: {action} | Konfidensi: {min(confidence, 99.9):.1f}%")
        
        return {
            "action": action,
            "confidence": min(confidence, 99.9),
            "sl_distance": sl_distance,
            "current_price": current_price
        }