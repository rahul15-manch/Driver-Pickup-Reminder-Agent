import logging
from app.reminder import build_reminder_message
from app.twilio_service import make_call
import os
import app.config

# Setup basic console logging for the test
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def test_reminder_logic():
    print("--- Running Deterministic Reminder Generation Tests ---")
    
    # Test 1 - Complete ride
    ride_1 = {
        "driver_name": "Rahul",
        "driver_phone": "+919999999999",
        "pickup_location": "Delhi Airport",
        "scheduled_pickup_time": "2026-08-19 10:30:00"
    }
    msg_1 = build_reminder_message(ride_1)
    print("\nTest 1 - Complete Ride:")
    print(msg_1)
    assert "Rahul" in msg_1
    assert "Delhi Airport" in msg_1
    assert "10:30 AM" in msg_1
    
    # Test 2 - Missing driver name
    ride_2 = {
        "pickup_location": "Delhi Airport",
        "scheduled_pickup_time": "2026-08-19 10:30:00"
    }
    msg_2 = build_reminder_message(ride_2)
    print("\nTest 2 - Missing Driver Name:")
    print(msg_2)
    assert "None" not in msg_2
    assert "Hello Driver" in msg_2
    
    # Test 3 - Missing pickup location
    ride_3 = {
        "driver_name": "Rahul",
        "scheduled_pickup_time": "2026-08-19 10:30:00"
    }
    msg_3 = build_reminder_message(ride_3)
    print("\nTest 3 - Missing Pickup Location:")
    print(msg_3)
    assert "None" not in msg_3
    assert "your scheduled pickup location" in msg_3
    
    # Test 4 - Invalid pickup time
    ride_4 = {
        "driver_name": "Rahul",
        "pickup_location": "Delhi Airport",
        "scheduled_pickup_time": "not-a-date"
    }
    msg_4 = build_reminder_message(ride_4)
    print("\nTest 4 - Invalid Pickup Time:")
    print(msg_4)
    assert "None" not in msg_4
    assert "your scheduled time" in msg_4
    
    print("\n--- Running Mock Twilio Call Test ---")
    # Test 5 - Twilio Mock
    import app.twilio_service
    app.twilio_service.MOCK_TWILIO = True
    
    test_phone = "+919999999999"
    print(f"Executing make_call({test_phone}, msg_1) with MOCK_TWILIO=True")
    sid = make_call(test_phone, msg_1)
    print(f"Resulting SID: {sid}")
    assert sid == "MOCK_SID_12345"

if __name__ == "__main__":
    test_reminder_logic()
    print("\nAll deterministic tests completed successfully.")
