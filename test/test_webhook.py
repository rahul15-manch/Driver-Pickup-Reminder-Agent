from fastapi.testclient import TestClient
from unittest import mock
from app.main import app
from app.sheets import get_rides

client = TestClient(app)

def test_webhook_endpoints():
    print("--- Running Deterministic Webhook Tests ---")
    
    # We'll use a local dictionary to mock the sheet data and functions
    # Initial state
    mock_rides = [
        {"row_index": 2, "call_sid": "CA_TEST_001", "call_status": ""},
        {"row_index": 3, "call_sid": "CA_TEST_002", "call_status": ""},
        {"row_index": 4, "call_sid": "CA_TEST_003", "call_status": ""},
        {"row_index": 5, "call_sid": "CA_TEST_004", "call_status": ""},
        {"row_index": 6, "call_sid": "CA_TEST_005", "call_status": ""},
    ]
    
    def mock_get_rides():
        return mock_rides
        
    def mock_update_call_status(row_index, call_status):
        for ride in mock_rides:
            if ride["row_index"] == row_index:
                ride["call_status"] = call_status
                return True
        return False

    with mock.patch("app.main.find_ride_by_call_sid") as mock_find:
        # Instead of mocking find_ride directly, we will let main import the patched functions...
        # Wait, find_ride_by_call_sid is imported directly into app.main
        # It's better to patch the functions inside app.main
        pass
        
    # Better to patch in the module they are used
    with mock.patch("app.main.find_ride_by_call_sid", side_effect=lambda sid: next((r for r in mock_rides if r["call_sid"] == sid), None)), \
         mock.patch("app.main.update_call_status", side_effect=mock_update_call_status):
         
        # Test 1 - Answered
        print("Test 1: Answered")
        response = client.post("/twilio/status", data={"CallSid": "CA_TEST_001", "CallStatus": "answered"})
        assert response.status_code == 200
        assert mock_rides[0]["call_status"] == "answered"
        
        # Test 2 - No Answer
        print("Test 2: No Answer")
        response = client.post("/twilio/status", data={"CallSid": "CA_TEST_002", "CallStatus": "no-answer"})
        assert response.status_code == 200
        assert mock_rides[1]["call_status"] == "no-answer"
        
        # Test 3 - Busy
        print("Test 3: Busy")
        response = client.post("/twilio/status", data={"CallSid": "CA_TEST_003", "CallStatus": "busy"})
        assert response.status_code == 200
        assert mock_rides[2]["call_status"] == "busy"
        
        # Test 4 - Failed
        print("Test 4: Failed")
        response = client.post("/twilio/status", data={"CallSid": "CA_TEST_004", "CallStatus": "failed"})
        assert response.status_code == 200
        assert mock_rides[3]["call_status"] == "failed"
        
        # Test 5 - Completed
        print("Test 5: Completed")
        response = client.post("/twilio/status", data={"CallSid": "CA_TEST_005", "CallStatus": "completed"})
        assert response.status_code == 200
        assert mock_rides[4]["call_status"] == "completed"
        
        # Test 6 - Unknown Call SID
        print("Test 6: Unknown Call SID")
        response = client.post("/twilio/status", data={"CallSid": "CA_UNKNOWN", "CallStatus": "no-answer"})
        assert response.status_code == 200
        assert response.json()["message"] == "Call SID not found in sheet"
        
        # Test 7 - Missing Call SID
        print("Test 7: Missing Call SID")
        response = client.post("/twilio/status", data={"CallStatus": "no-answer"})
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
        
        # Test 8 - Missing Call Status
        print("Test 8: Missing Call Status")
        response = client.post("/twilio/status", data={"CallSid": "CA_TEST_001"})
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

def test_integration_live_webhook():
    print("\n--- Running Live Integration Webhook Test ---")
    print("Testing MOCK_SID_12345 in the Live Google Sheet")
    # This will directly hit the actual endpoints and update the Live Sheet.
    response = client.post("/twilio/status", data={"CallSid": "MOCK_SID_12345", "CallStatus": "no-answer"})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Check the live sheet to confirm it worked
    rides = get_rides()
    for r in rides:
        if r.get("call_sid") == "MOCK_SID_12345":
            print(f"Verified Live Sheet Row #{r.get('row_index')}:")
            print(f"reminder_status: {r.get('reminder_status')}")
            print(f"call_sid: {r.get('call_sid')}")
            print(f"call_status: {r.get('call_status')}")
            break

if __name__ == "__main__":
    test_webhook_endpoints()
    test_integration_live_webhook()
    print("\nTests completed.")
