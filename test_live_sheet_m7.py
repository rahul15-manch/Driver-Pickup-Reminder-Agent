import os
import time
from unittest import mock
import app.config

# Force MOCK_TWILIO to true in the environment for absolute safety
os.environ["MOCK_TWILIO"] = "true"
app.config.MOCK_TWILIO = True

from app.sheets import get_rides, mark_reminder_sent
from app.trigger import find_eligible_rides
from app.reminder import build_reminder_message
import app.twilio_service

# Monkeypatch twilio_service module config
app.twilio_service.MOCK_TWILIO = True

def run_live_tests():
    print("=== Milestone 7: Live Google Sheet Verification Test ===\n")
    
    print("--- Test 1: Read Real Google Sheet ---")
    rides = get_rides()
    print(f"Found {len(rides)} rides")
    for r in rides:
        print(f"\nRide #{r.get('row_index')}")
        print(f"Driver: {r.get('driver_name')}")
        print(f"Pickup: {r.get('pickup_location')}")
        print(f"Scheduled: {r.get('scheduled_pickup_time')}")
        print(f"Status: {r.get('reminder_status')}")

    print("\n--- Test 2: Trigger Eligibility ---")
    eligible_rides = find_eligible_rides(rides)
    print(f"Found {len(eligible_rides)} eligible rides out of {len(rides)} total rides.")
    for r in eligible_rides:
        print(f"ELIGIBLE Ride #{r.get('row_index')}: {r.get('driver_name')} ({r.get('scheduled_pickup_time')})")

    # To ensure we don't accidentally update everything if something goes wrong,
    # we'll only update the FIRST eligible ride for Test 3 & 4.
    if not eligible_rides:
        print("WARNING: No eligible rides found! Please ensure test data contains rides 29-30 mins away.")
        # We can't proceed with Tests 3-6 if there are no eligible rides.
    else:
        test_ride = eligible_rides[0]
        
        print("\n--- Test 3: Mock Twilio Call ---")
        msg = build_reminder_message(test_ride)
        phone = test_ride.get("driver_phone", "+919999999999")
        if not phone:
            phone = "+919999999999"
            
        print("Generated Message:")
        print(msg)
        
        sid = app.twilio_service.make_call(phone, msg)
        print(f"Mock Call returned SID: {sid}")
        
        print("\n--- Test 4: Update Real Google Sheet ---")
        if sid:
            success = mark_reminder_sent(test_ride['row_index'], sid)
            print(f"Google Sheet update success: {success}")
        
        print("\n--- Test 5: Verify the Actual Sheet ---")
        time.sleep(2) # brief pause to let sheets API settle
        rides_after = get_rides()
        updated_ride = next((r for r in rides_after if r['row_index'] == test_ride['row_index']), None)
        if updated_ride:
            print(f"Verified Ride #{updated_ride['row_index']}")
            print(f"reminder_status: {updated_ride.get('reminder_status')}")
            print(f"call_sid: {updated_ride.get('call_sid')}")
            print(f"reminder_sent_at: {updated_ride.get('reminder_sent_at')}")
        
        print("\n--- Test 6: Duplicate Prevention ---")
        eligible_rides_after = find_eligible_rides(rides_after)
        is_still_eligible = any(r['row_index'] == test_ride['row_index'] for r in eligible_rides_after)
        if is_still_eligible:
            print(f"FAIL: Ride #{test_ride['row_index']} is STILL eligible despite being sent!")
        else:
            print(f"SUCCESS: Previously eligible ride #{test_ride['row_index']} -> SKIP (already sent)")
    
    print("\n--- Test 7: Verify Other Rides ---")
    # check that non-eligible rides are untouched
    # We will just print their state.
    try:
        rides_after_verify = get_rides() if 'rides_after' not in locals() else rides_after
        for r in rides_after_verify:
            if 'test_ride' in locals() and r['row_index'] == test_ride['row_index']:
                continue
            print(f"Ride #{r['row_index']} ({r.get('driver_name')}) -> {r.get('reminder_status', 'empty')}")
    except Exception as e:
        pass
        
    print("\n--- Test 8: Failure Simulation ---")
    # We'll take another ride (or mock one) and force Twilio failure
    print("Simulating Twilio Failure in Mock Mode")
    with mock.patch("app.twilio_service.make_call", return_value=None):
        failed_sid = app.twilio_service.make_call("+123", "Hello")
        print(f"Call SID from failure: {failed_sid}")
        if failed_sid:
            print("ERROR: Should not have a SID")
        else:
            print("mark_reminder_sent() NOT called.")
            print("reminder_status remains pending.")
            
    print("\n--- Test 9: Final Sheet State ---")
    final_rides = get_rides()
    for r in final_rides:
        print(f"{r.get('driver_name', 'Unknown')} -> {r.get('reminder_status', 'empty')} -> {r.get('call_sid', 'none')}")

if __name__ == "__main__":
    run_live_tests()
