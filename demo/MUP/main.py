import requests
import time
import sys

# ------------------------------------------------------------
# API endpoints (adjust BASE_URL if needed)
# ------------------------------------------------------------
BASE_URL = "http://localhost:3001"

def get_price(symbol):
    """Fetch the last price for the given symbol."""
    url = f"{BASE_URL}/api/stats/{symbol}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return float(data['last_price'])

def get_balance(token):
    """Get the full balance (USDT and all coins)."""
    url = f"{BASE_URL}/api/user/{token}/balance"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def buy_market(symbol, usdt_amount, token):
    """
    Place a market buy order.
    Returns the quantity of coin actually bought (based on balance change).
    """
    before = get_balance(token)
    before_coin = before['coins'].get(symbol, 0.0)

    url = f"{BASE_URL}/api/user/{token}/spot/buy/market/{symbol}?amount={usdt_amount}"
    resp = requests.post(url)
    resp.raise_for_status()

    after = get_balance(token)
    after_coin = after['coins'].get(symbol, 0.0)

    filled = after_coin - before_coin
    if filled < 0:
        print(f"Warning: balance decreased? before={before_coin}, after={after_coin}")
    return filled

def sell_market(symbol, coin_amount, token):
    """Place a market sell order for a specific coin amount."""
    url = f"{BASE_URL}/api/user/{token}/spot/sell/market/{symbol}?amount={coin_amount}"
    resp = requests.post(url)
    resp.raise_for_status()
    return resp.json()

# ------------------------------------------------------------
# Helper: reset grid with new price
# ------------------------------------------------------------
def reset_grid(current_price, symbol, grids, grid_percent, amount_per_buy, token):
    """Recalculate grid levels and reset state arrays."""
    step = current_price * (grid_percent / 100.0)
    middle_index = grids // 2
    all_levels = [current_price + i * step for i in range(grids)]
    buy_levels = all_levels[:middle_index]
    middle_level = all_levels[middle_index]
    sell_levels = all_levels[middle_index+1:]

    num_buys = len(buy_levels)
    num_sells = len(sell_levels)

    buy_quantities = [None] * num_buys
    buy_done = [False] * num_buys
    sell_done = [False] * num_sells

    # Perform initial buy at grid 1 (current price)
    print(f"\n[RESET] Initial buy at current price {current_price:.2f} ...")
    try:
        qty = buy_market(symbol, amount_per_buy, token)
        buy_quantities[0] = qty
        buy_done[0] = True
        print(f"Bought {qty:.8f} {symbol}")
    except Exception as e:
        print(f"Initial buy failed: {e}")
        sys.exit(1)

    balance = get_balance(token)
    print(f"Balance after initial buy: {balance}")

    return {
        'all_levels': all_levels,
        'buy_levels': buy_levels,
        'middle_level': middle_level,
        'sell_levels': sell_levels,
        'buy_quantities': buy_quantities,
        'buy_done': buy_done,
        'sell_done': sell_done,
        'num_buys': num_buys,
        'num_sells': num_sells,
        'middle_index': middle_index
    }

# ------------------------------------------------------------
# User inputs
# ------------------------------------------------------------
token = input("Enter your API token: ").strip()
if not token:
    print("Token cannot be empty.")
    sys.exit(1)

symbol = input("Enter symbol (e.g., BTC): ").strip().upper()
if not symbol:
    print("Symbol cannot be empty.")
    sys.exit(1)

grids = int(input("Input how many grids you want (must be odd): "))
if grids % 2 == 0:
    print("Number of grids must be odd. Please restart the program.")
    sys.exit(1)

grid_percent = float(input("Input grid %: "))
amount_per_buy = float(input("Enter USDT amount for each buy: "))

# ------------------------------------------------------------
# Initial setup
# ------------------------------------------------------------
try:
    price = get_price(symbol)
except Exception as e:
    print(f"Error fetching price: {e}")
    sys.exit(1)

# Display initial grid info
step = price * (grid_percent / 100.0)
middle_index = grids // 2
all_levels = [price + i * step for i in range(grids)]
print("\n--- Grid Levels ---")
for i, level in enumerate(all_levels, start=1):
    if i - 1 < middle_index:
        label = "BUY"
    elif i - 1 == middle_index:
        label = "no action"
    else:
        label = "SELL"
    if level.is_integer():
        print(f"grid {i} : {int(level)} ({label})")
    else:
        print(f"grid {i} : {level:.2f} ({label})")
print("--------------------\n")

# Initialize grid state
state = reset_grid(price, symbol, grids, grid_percent, amount_per_buy, token)

# ------------------------------------------------------------
# Main monitoring loop
# ------------------------------------------------------------
print("\nStarting price monitoring (check every 1 second)...")
print("Press Ctrl+C to stop.\n")

phase = 'active'          # 'active' or 'waiting_drop'
max_price_since_completion = None

try:
    while True:
        current_price = get_price(symbol)

        # ------------------------------------------------------------------
        # PHASE: WAITING FOR DROP
        # ------------------------------------------------------------------
        if phase == 'waiting_drop':
            # Update max price seen since entering this phase
            if max_price_since_completion is None or current_price > max_price_since_completion:
                max_price_since_completion = current_price

            drop_pct = (max_price_since_completion - current_price) / max_price_since_completion
            status = f"Current price: {current_price:.2f} | Waiting for drop ≥ 0.5% from {max_price_since_completion:.2f} (current drop: {drop_pct*100:.2f}%)"
            print(f"\r{status}", end="")

            if drop_pct >= 0.005:
                print(f"\nDrop of {drop_pct*100:.2f}% detected – resetting grid at current price {current_price:.2f}")
                # Reset grid with current price
                state = reset_grid(current_price, symbol, grids, grid_percent, amount_per_buy, token)
                phase = 'active'
                max_price_since_completion = None
                # Continue loop – we'll now handle active phase
                continue
            else:
                time.sleep(1)
                continue

        # ------------------------------------------------------------------
        # PHASE: ACTIVE TRADING
        # ------------------------------------------------------------------
        # Extract state variables
        buy_levels = state['buy_levels']
        sell_levels = state['sell_levels']
        buy_done = state['buy_done']
        sell_done = state['sell_done']
        buy_quantities = state['buy_quantities']
        middle_index = state['middle_index']
        num_buys = state['num_buys']
        num_sells = state['num_sells']
        middle_level = state['middle_level']

        # Determine next actions for display
        next_buy = None
        for idx in range(num_buys):
            if not buy_done[idx]:
                next_buy = buy_levels[idx]
                break

        next_sell = None
        for idx in range(num_sells):
            if not sell_done[idx]:
                buy_idx = middle_index - 1 - idx
                if buy_idx >= 0 and buy_quantities[buy_idx] is not None:
                    next_sell = sell_levels[idx]
                    break

        # Build status line
        status = f"Current price: {current_price:.2f}"
        if next_buy is not None:
            status += f" | Next buy at: {next_buy:.2f}"
        if next_sell is not None:
            status += f" | Next sell at: {next_sell:.2f}"
        if next_buy is None and next_sell is None:
            status += " | All actions completed. Waiting for drop..."
        print(f"\r{status}", end="")

        # Check if all actions are completed -> switch to waiting phase
        all_buy_done = all(buy_done)
        all_sell_done = all(sell_done)
        if all_buy_done and all_sell_done:
            print("\nAll actions completed – entering wait-for-drop mode.")
            phase = 'waiting_drop'
            max_price_since_completion = current_price
            # Continue to next loop iteration (will go to waiting phase)
            time.sleep(1)
            continue

        # ---------- Execute BUY levels ----------
        for idx, level in enumerate(buy_levels):
            if not buy_done[idx] and current_price >= level:
                print(f"\nPrice {current_price:.2f} reached buy level {level:.2f} → buying ...")
                try:
                    qty = buy_market(symbol, amount_per_buy, token)
                    buy_quantities[idx] = qty
                    buy_done[idx] = True
                    print(f"Bought {qty:.8f} {symbol}")
                    balance = get_balance(token)
                    print(f"Updated balance: {balance}")
                except Exception as e:
                    print(f"Buy failed at level {level:.2f}: {e}")

        # ---------- Execute SELL levels ----------
        for idx, level in enumerate(sell_levels):
            if not sell_done[idx]:
                buy_idx = middle_index - 1 - idx
                if buy_idx >= 0 and buy_quantities[buy_idx] is not None and buy_quantities[buy_idx] > 0:
                    if current_price >= level:
                        sell_amount = buy_quantities[buy_idx]
                        print(f"\nPrice {current_price:.2f} reached sell level {level:.2f} → selling {sell_amount:.8f} {symbol} ...")
                        try:
                            sell_market(symbol, sell_amount, token)
                            sell_done[idx] = True
                            print(f"Sold {sell_amount:.8f} {symbol}")
                            balance = get_balance(token)
                            print(f"Updated balance: {balance}")
                        except Exception as e:
                            print(f"Sell failed at level {level:.2f}: {e}")

        # Update state (arrays are mutable, but we reassign to keep reference)
        state['buy_quantities'] = buy_quantities
        state['buy_done'] = buy_done
        state['sell_done'] = sell_done

        time.sleep(1)

except KeyboardInterrupt:
    print("\nMonitoring stopped by user.")
except Exception as e:
    print(f"\nUnexpected error: {e}")

print("Program ended.")