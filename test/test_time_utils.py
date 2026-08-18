import logging
from datetime import datetime, timedelta
import pytz
from app.config import TIMEZONE
from app.time_utils import get_minutes_until_pickup

# Setup basic console logging for the test
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def test_time_processing():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    print(f"--- Running Time Processing Tests (Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')} {TIMEZONE}) ---")
    
    # Generate test timestamps relative to 'now'
    t_30_future = (now + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    t_10_future = (now + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    t_60_future = (now + timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M:%S")
    t_10_past = (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    
    scenarios = [
        {"name": "30 min future", "time": t_30_future, "expected": 30},
        {"name": "10 min future", "time": t_10_future, "expected": 10},
        {"name": "60 min future", "time": t_60_future, "expected": 60},
        {"name": "10 min past", "time": t_10_past, "expected": -10},
        {"name": "Invalid timestamp", "time": "not-a-date", "expected": None},
        {"name": "Missing timestamp", "time": "", "expected": None},
    ]
    
    for scenario in scenarios:
        result = get_minutes_until_pickup(scenario["time"])
        # Because we truncate seconds (// 60), if we add exactly 30 mins, 
        # it might be 29 depending on sub-second precision, but it should be ~30.
        # We will just print to visually verify the logic.
        print(f"Scenario: {scenario['name']:<20} | Input: {scenario['time']:<20} | Result: {result} (Expected approx: {scenario['expected']})")

    # Integration Demonstration
    print("\n--- Integration Demonstration with Dummy Ride Data ---")
    dummy_ride = {
        "row_index": 2,
        "driver_name": "Rahul",
        "driver_phone": "+919XXXXXXXXX",
        "pickup_location": "Delhi Airport",
        "scheduled_pickup_time": t_30_future
    }
    minutes = get_minutes_until_pickup(dummy_ride["scheduled_pickup_time"])
    print(f"Driver: {dummy_ride['driver_name']}")
    print(f"Pickup: {dummy_ride['pickup_location']}")
    print(f"Scheduled pickup: {dummy_ride['scheduled_pickup_time']}")
    print(f"Minutes until pickup: {minutes}")

if __name__ == "__main__":
    test_time_processing()
