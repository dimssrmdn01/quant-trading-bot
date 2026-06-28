# MT5 Quant Trading Engine (Lasso ML)

An autonomous, end-to-end quantitative trading bot designed for MetaTrader 5. This engine performs real-time market data ingestion, dynamic feature engineering, and predictive modeling using Lasso Regression to execute trades with strict risk management protocols.

##Core Architecture

* **Dynamic Machine Learning:** Unlike static models, this bot uses **Online Learning**. It retrains its Lasso Regression model on the fly using the latest 200 candlesticks before making any trading decision.
* **Noise Filtering via MSE:** Trades are only executed if the model's Mean Squared Error (MSE) is strictly below the market's current volatility threshold (1.5x ATR). If the market is too choppy, the bot forces a `HOLD` position.
* **Institutional Risk Management:** Automatically calculates safe lot sizes based on a strict 1% equity risk rule and dynamic Stop Loss distances derived from the Average True Range (ATR).
* **Direct Broker Execution:** Bypasses slow APIs by communicating directly with the MetaTrader 5 terminal locally or on a VPS.

##Tech Stack
* **Language:** Python 3.x
* **Trading Terminal:** MetaTrader 5 (via `MetaTrader5` library)
* **Machine Learning:** `scikit-learn` (Lasso Regression, StandardScaler, MSE validation)
* **Data Manipulation:** `pandas`, `numpy`

##Quick Start Guide

### 1. Prerequisites
Ensure you have the MetaTrader 5 desktop terminal installed and logged into your broker account (e.g., Exness).

### 2. Installation
Clone the repository and install the required dependencies:

    git clone https://github.com/dimssrmdn01/quant-trading-bot.git
    cd quant-trading-bot
    pip install MetaTrader5 pandas numpy scikit-learn

### 3. Configuration
For security reasons, credentials are not tracked in this repository. You must create a keys.json file inside a config directory:

1. Create a folder named `config`.
2. Create a file named `keys.json` inside it and add your MT5 credentials:

    {
        "account": 12345678,
        "password": "YOUR_MT5_PASSWORD",
        "server": "Exness-MT5Trial"
    }

### 4. Running the Autopilot
Launch the main orchestration script. The bot will wake up every 15 minutes, scan the market, train the model, execute trades if conditions are met, and go back to sleep.

    python main.py

---
##Disclaimer
This software is for educational and research purposes only. Do not use it to trade with real money unless you fully understand the risks involved in algorithmic trading.
