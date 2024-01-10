import os
import datetime
import pytz
from dotenv import load_dotenv

def find_latest_files(pattern, count=2):
    """Find the latest files based on the date in the filename."""
    path = './orders/'
    files = sorted([f for f in os.listdir(path) if f.startswith(pattern)], key=lambda x: x.split('_')[1], reverse=True)
    return [path + f for f in files[:count]]

def read_positions(full_path):
    """Read the positions from a file."""
    positions = {}
    if os.path.exists(full_path):
        with open(full_path, 'r') as file:
            next(file)  # Skip header
            for line in file:
                parts = line.strip().split(',')
                positions[parts[1]] = int(parts[0])
    return positions

def calculate_orders(current_positions, previous_positions):
    """Calculate the orders based on the changes in positions."""
    orders = []
    all_symbols = set(current_positions.keys()).union(previous_positions.keys())
    for symbol in all_symbols:
        current_qty = current_positions.get(symbol, 0)
        previous_qty = previous_positions.get(symbol, 0)
        qty_change = current_qty - previous_qty
        if qty_change != 0:
            action = 'BUY' if qty_change > 0 else 'SELL'
            orders.append((action, abs(qty_change), symbol))
    return orders

def get_eastern_time_plus_minutes(order_date, minutes):
    """Get current time in US Eastern time zone, plus minutes."""
    eastern = pytz.timezone('US/Eastern')
    now_eastern = datetime.datetime.now(datetime.timezone.utc).astimezone(eastern)
    order_datetime = datetime.datetime.strptime(order_date, '%Y%m%d')
    combined_datetime = now_eastern.replace(year=order_datetime.year, month=order_datetime.month, day=order_datetime.day)
    later = combined_datetime + datetime.timedelta(minutes=minutes)
    return later.strftime('%Y%m%d %H:%M:00 US/Eastern')

def write_orders(orders, filename, order_date, account):
    """Write the orders to a file with additional fields."""
    path = './orders/'
    full_path = path + filename
    header = "Action,Quantity,Symbol,SecType,Exchange,Currency,TimeInForce,OrderType,BasketTag,Account,OrderRef,Algo allowPastEndTime,Algo catchUp,Algo endTime,Algo strategy\n"
    algo_end_time = get_eastern_time_plus_minutes(order_date, 20)
    with open(full_path, 'w') as file:
        file.write(header)
        for order in orders:
            file.write(','.join(map(str, order)) + ",STK,SMART/AMEX,USD,DAY,MKT,Basket," + account + ",Basket,TRUE,FALSE," + algo_end_time + ",Twap\n")

def main():
    load_dotenv()
    account = os.environ['IB_ACCOUNT']

    latest_files = find_latest_files('positions_')
    latest_positions_file = latest_files[0]
    previous_positions_file = latest_files[1] if len(latest_files) > 1 else None

    current_positions = read_positions(latest_positions_file)
    previous_positions = read_positions(previous_positions_file) if previous_positions_file else {}
    print(current_positions)
    print(previous_positions)

    orders = calculate_orders(current_positions, previous_positions)
    order_date = latest_positions_file.split('_')[1].split('.')[0]
    orders_filename = 'orders_' + order_date + '.csv'
    write_orders(orders, orders_filename, order_date, account)

if __name__ == "__main__":
    main()
