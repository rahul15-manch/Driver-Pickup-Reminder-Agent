import os
import time
from unittest import mock
import app.config
import app.twilio_service

app.config.MOCK_TWILIO = True
app.twilio_service.MOCK_TWILIO = True
os.environ["MOCK_TWILIO"] = "true"

from app.sheets import get_rides, mark_reminder_sent, update_call_status
from app.time_utils import get_minutes_until_pickup
from app.trigger import find_eligible_rides
from app.reminder import build_reminder_message
from app.scheduler import run_scheduler_cycle
from fastapi.testclient import TestClient
from app.main import app as fastapi_app

client = TestClient(fastapi_app)

def run_rehearsal():
    print("==================================================")
    print("TEST 1 — GOOGLE SHEET INPUT")
    print("==================================================")
    rides = get_rides()
    test_ride = None
    for r in rides:
        if r.get("driver_name") == "Demo Test Driver":
            test_ride = r
            break
            
    if test_ride:
        print(f"Driver:\n{test_ride.get('driver_name')}\n")
        print(f"Pickup:\n{test_ride.get('pickup_location')}\n")
        print(f"Status:\n{test_ride.get('reminder_status')}\n")
    else:
        print("ERROR: Demo Test Driver not found.")
        return

    print("==================================================")
    print("TEST 2 — TIME PROCESSING")
    print("==================================================")
    mins = get_minutes_until_pickup(test_ride.get("scheduled_pickup_time"))
    print(f"Minutes until pickup: {mins}")
    print(f"Expected: 29 <= {mins} <= 30\n")

    print("==================================================")
    print("TEST 3 — ELIGIBILITY")
    print("==================================================")
    eligible = find_eligible_rides(rides)
    print("Eligible rides found:")
    for r in eligible:
        print(f"{r.get('driver_name')} -> ELIGIBLE\n")

    print("==================================================")
    print("TEST 4 — DYNAMIC MESSAGE")
    print("==================================================")
    msg = build_reminder_message(test_ride)
    print("Generated Message:")
    print(f'"{msg}"\n')

    print("==================================================")
    print("TEST 5 — MOCK TWILIO & TEST 6 — REAL GOOGLE SHEET UPDATE")
    print("==================================================")
    print("Running one scheduler cycle...")
    run_scheduler_cycle()
    time.sleep(2) # Allow sheets API to settle
    
    print("\nVerifying Real Google Sheet Update...")
    rides_after = get_rides()
    updated_ride = next((r for r in rides_after if r.get('driver_name') == "Demo Test Driver"), None)
    print(f"reminder_status = {updated_ride.get('reminder_status')}")
    print(f"call_sid = {updated_ride.get('call_sid')}")
    print(f"reminder_sent_at = {updated_ride.get('reminder_sent_at')}\n")

    print("==================================================")
    print("TEST 7 — DUPLICATE PREVENTION")
    print("==================================================")
    print("Running scheduler cycle again immediately...")
    run_scheduler_cycle()
    print("Expected: Demo Test Driver -> SKIP -> No second Mock Twilio call\n")

    print("==================================================")
    print("TEST 8 — CALL STATUS WEBHOOK")
    print("==================================================")
    sid = updated_ride.get('call_sid')
    if sid:
        print(f"Simulating Webhook: CallSid = {sid}, CallStatus = answered")
        client.post("/twilio/status", data={"CallSid": sid, "CallStatus": "answered"})
        r_answered = next((r for r in get_rides() if r.get('driver_name') == "Demo Test Driver"), None)
        print(f"Verified call_status = {r_answered.get('call_status')}")
        
        print(f"\nSimulating Webhook: CallSid = {sid}, CallStatus = completed")
        client.post("/twilio/status", data={"CallSid": sid, "CallStatus": "completed"})
        r_completed = next((r for r in get_rides() if r.get('driver_name') == "Demo Test Driver"), None)
        print(f"Verified call_status = {r_completed.get('call_status')}")
        print(f"Verified reminder_status remains = {r_completed.get('reminder_status')}\n")
    else:
        print("ERROR: Call SID is missing, cannot test webhook.")

    print("==================================================")
    print("TEST 9 — FAILURE SCENARIO")
    print("==================================================")
    # Set up a fake row in memory for test
    fake_ride = {"row_index": 99, "driver_name": "Fail Test", "driver_phone": "+1", "scheduled_pickup_time": test_ride.get("scheduled_pickup_time"), "reminder_status": "pending"}
    def mock_get_rides(): return [fake_ride]
    def mock_mark_sent(row, sid): fake_ride["reminder_status"] = "sent"; return True
    
    with mock.patch("app.scheduler.get_rides", side_effect=mock_get_rides), \
         mock.patch("app.scheduler.mark_reminder_sent", side_effect=mock_mark_sent), \
         mock.patch("app.scheduler.make_call", return_value=None):
        print("Running mock Twilio failure...")
        run_scheduler_cycle()
        print(f"Verified reminder_status remains: {fake_ride['reminder_status']}\n")

if __name__ == "__main__":
    run_rehearsal()
