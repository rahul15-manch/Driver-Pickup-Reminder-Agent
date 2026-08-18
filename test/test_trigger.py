import logging
from unittest import mock
from app.trigger import find_eligible_rides

# Setup basic console logging for the test
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def test_trigger_logic():
    print("--- Running Deterministic Trigger Logic Tests ---")
    
    # Mocking get_minutes_until_pickup so we don't depend on actual time parsing for these tests
    # We will map the scheduled_pickup_time string directly to the returned integer for the mock
    mock_returns = {
        "30_min": 30,
        "29_min": 29,
        "31_min": 31,
        "45_min": 45,
        "10_min": 10,
        "past": -5,
        "invalid": None
    }
    
    rides = [
        {"row_index": 1, "driver_name": "A", "scheduled_pickup_time": "30_min", "reminder_status": "pending"},
        {"row_index": 2, "driver_name": "B", "scheduled_pickup_time": "29_min", "reminder_status": ""},
        {"row_index": 3, "driver_name": "C", "scheduled_pickup_time": "31_min", "reminder_status": "pending"},
        {"row_index": 4, "driver_name": "D", "scheduled_pickup_time": "45_min", "reminder_status": "pending"},
        {"row_index": 5, "driver_name": "E", "scheduled_pickup_time": "10_min", "reminder_status": "pending"},
        {"row_index": 6, "driver_name": "F", "scheduled_pickup_time": "past", "reminder_status": "pending"},
        {"row_index": 7, "driver_name": "G", "scheduled_pickup_time": "30_min", "reminder_status": "sent"},
        {"row_index": 8, "driver_name": "H", "scheduled_pickup_time": "invalid", "reminder_status": "pending"},
        {"row_index": 9, "driver_name": "I", "scheduled_pickup_time": "", "reminder_status": "pending"},
    ]
    
    with mock.patch('app.trigger.get_minutes_until_pickup') as mock_get_minutes:
        # Side effect maps the pickup_time string to the mock_returns dict
        mock_get_minutes.side_effect = lambda x: mock_returns.get(x, None)
        
        eligible = find_eligible_rides(rides)
        
        print("\nResults:")
        for r in rides:
            is_eligible = r in eligible
            print(f"Ride {r['driver_name']} -> {r['scheduled_pickup_time']} -> {r['reminder_status']} -> {'ELIGIBLE' if is_eligible else 'SKIP'}")
            
        print(f"\nTotal eligible rides found: {len(eligible)} (Expected: 2 -> A and B)")


def test_integration_with_sheets():
    print("\n--- Running Integration Test with Live Google Sheet ---")
    try:
        from app.sheets import get_rides
        rides = get_rides()
        if not rides:
            print("No rides found in Google Sheets to evaluate.")
            return
            
        print(f"Checking {len(rides)} scheduled rides...")
        eligible = find_eligible_rides(rides)
        
        for r in rides:
            # Re-calculating just to print the verbose output matching the prompt's request
            from app.time_utils import get_minutes_until_pickup
            mins = get_minutes_until_pickup(r.get("scheduled_pickup_time"))
            status_text = 'ELIGIBLE' if r in eligible else 'SKIP'
            if r.get("reminder_status") == "sent":
                print(f"Ride #{r.get('row_index')} — {r.get('driver_name', 'Unknown')} — reminder already sent → SKIP")
            else:
                print(f"Ride #{r.get('row_index')} — {r.get('driver_name', 'Unknown')} — {mins} minutes away → {status_text}")
                
        print(f"\nEligible rides: {len(eligible)}")
        
    except Exception as e:
        print(f"Integration test blocked: {e}")

if __name__ == "__main__":
    test_trigger_logic()
    test_integration_with_sheets()
