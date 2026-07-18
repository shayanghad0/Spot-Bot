import requests
import sys

# Ask user for inputs
symbol = input("Enter symbol (e.g., BTC): ")
grids = int(input("Input how many grids you want: "))
grid_percent = float(input("Input grid %: "))

# Validate that number of grids is odd
if grids % 2 == 0:
    print("Number of grids must be odd. Please restart the program.")
    sys.exit(1)

# Fetch the last price from the API
try:
    response = requests.get(f"http://localhost:3001/api/stats/{symbol}")
    response.raise_for_status()          # Raise exception for HTTP errors
    data = response.json()
    price = data.get('last_price')       # Extract the last_price field
    if price is None:
        print("Error: 'last_price' not found in API response.")
        sys.exit(1)
    price = float(price)
except Exception as e:
    print(f"Error fetching price: {e}")
    sys.exit(1)

# Calculate grid levels
step = price * (grid_percent / 100)
middle_index = grids // 2

# Generate and display each grid level
for i in range(1, grids + 1):
    level = price + (i - 1) * step

    # Determine if BUY, SELL, or no buy or sell
    if i - 1 < middle_index:
        label = "BUY"
    elif i - 1 == middle_index:
        label = "no buy or sell"
    else:
        label = "SELL"

    # Output with proper formatting
    if level.is_integer():
        print(f"grid {i} : {int(level)} ({label})")
    else:
        print(f"grid {i} : {level:.2f} ({label})")