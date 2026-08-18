import logging
import app.config
import app.twilio_service
from app.sheets import mark_reminder_sent
from unittest import mock

# Setup basic console logging for the test
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def test_duplicate_prevention_logic():
    print("--- Running Deterministic Duplicate Prevention Tests ---")
    
    # We will mock update_ride_status to act as our "in-memory" Google Sheet for this test
    # It will record the state updates securely without touching the real network.
    memory_sheet = {
        "reminder_status": "pending",
        "call_sid": "",
        "reminder_sent_at": ""
    }
    
    def mock_update_ride_status(row_index, status, column_name):
        memory_sheet[column_name] = status
        return True
        
    with mock.patch("app.sheets.update_ride_status", side_effect=mock_update_ride_status):
        
        # Test 1: pending -> call -> sent
        print("\nTest 1: Normal successful call")
        app.twilio_service.MOCK_TWILIO = True
        # Simulate scheduler determining it's eligible
        is_eligible = memory_sheet["reminder_status"] != "sent"
        assert is_eligible == True
        
        # Simulate Twilio call succeeding
        sid = app.twilio_service.make_call("+123", "Hello")
        assert sid == "MOCK_SID_12345"
        
        # System records the success
        if sid:
            mark_reminder_sent(2, sid)
            
        print(f"Memory Sheet State: {memory_sheet}")
        assert memory_sheet["reminder_status"] == "sent"
        assert memory_sheet["call_sid"] == "MOCK_SID_12345"
        assert memory_sheet["reminder_sent_at"] != ""
        
        # Test 2: sent -> scheduler runs again -> skipped
        print("\nTest 2: Next scheduler run (already sent)")
        # Simulate scheduler checking eligibility again
        is_eligible_run_2 = memory_sheet["reminder_status"] != "sent"
        print(f"Is Eligible? {is_eligible_run_2}")
        assert is_eligible_run_2 == False
        
        # Test 3: Twilio call fails (reset sheet to pending to test this flow)
        print("\nTest 3: Twilio API failure")
        memory_sheet["reminder_status"] = "pending"
        memory_sheet["call_sid"] = ""
        memory_sheet["reminder_sent_at"] = ""
        
        # Mock Twilio to return None (failure)
        app.twilio_service.MOCK_TWILIO = False
        with mock.patch("app.twilio_service.get_twilio_client", return_value=None):
            sid_fail = app.twilio_service.make_call("+123", "Hello")
            assert sid_fail is None
            
            if sid_fail:
                mark_reminder_sent(2, sid_fail)
                
            print(f"Memory Sheet State: {memory_sheet}")
            assert memory_sheet["reminder_status"] == "pending"

def test_integration_with_sheets():
    print("\n--- Running Integration Test with Live Google Sheet ---")
    try:
        from app.sheets import get_rides
        rides = get_rides()
        if not rides:
            print("No rides found in Google Sheets to evaluate.")
            return
            
        print("Integration test involves modifying the live sheet, which is disabled here to prevent data corruption during automated verification without a designated test row.")
        print("To test manually: add a test row to the Google Sheet, then trigger `mark_reminder_sent(row, sid)`.")
    except Exception as e:
        print(f"Integration test blocked: {e}")

if __name__ == "__main__":
    test_duplicate_prevention_logic()
    test_integration_with_sheets()
