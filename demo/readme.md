# Bit24 Trading Bot – Demo

> **⚠️ IMPORTANT**  
> This is a **demo** version intended **only for testing** whether the logic works.  
> The actual Bit24 API endpoints used here are **private** and **not accessible** in this demo.  
> For the **real production code** that works with the Bit24 exchange, please check the **`real/`** folder.

---

## What it does

- Connects to a local mock API (`http://localhost:3001`)  
- Performs automatic buy/sell cycles based on price movements (drop, pump, profit target)  
- Records trades to `trade.json`  
- Generates a balance chart and a report (`trade_report.html`)

---

## Requirements

- Python 3.7+
- Install dependencies:
  ```bash
  pip install requests matplotlib
  ```

---

## How to run

1. Start your mock API server at `http://localhost:3001`.
2. Run the bot:
   ```bash
   python bot.py
   ```
3. Enter a symbol (e.g., `BTC`) and any API token (the token is not validated in the demo).
4. Press `Ctrl+C` at any time to stop and generate a report.

---

## Files generated

- `trade.json` – list of all orders  
- `balance_chart.png` – balance over time  
- `trade_report.html` – summary report with chart  

---

## Disclaimer

This code is **for demonstration purposes only**.  
Do not use it with real funds or real exchange accounts.  
The actual trading logic may differ in the production version.