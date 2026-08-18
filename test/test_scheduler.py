import logging
from unittest import mock
import app.config
import app.twilio_service
from app.scheduler import run_scheduler_cycle

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def test_scheduler_mock_flows():
    print("--- Running Deterministic Scheduler Tests ---")
    
    mock_rides = []
    
    def mock_get_rides():
        return mock_rides
        
    def mock_mark_sent(row, sid):
        for r in mock_rides:
            if r["row_index"] == row:
                r["reminder_status"] = "sent"
        return True
    
    with mock.patch("app.scheduler.get_rides", side_effect=mock_get_rides), \
         mock.patch("app.scheduler.mark_reminder_sent", side_effect=mock_mark_sent), \
         mock.patch("app.twilio_service.MOCK_TWILIO", True):
        
        # Ensure twilio uses mock natively
        app.config.MOCK_TWILIO = True
         
        # Test 1 - Empty Sheet
        print("\nTest 1 - Empty Sheet")
        run_scheduler_cycle()
        
        # Test 2 - One Eligible Ride
        print("\nTest 2 - One Eligible Ride")
        import pytz
        from datetime import datetime, timedelta
        tz = pytz.timezone(app.config.TIMEZONE)
        target = datetime.now(tz) + timedelta(minutes=29, seconds=30)
        time_str = target.strftime("%Y-%m-%d %H:%M:%S")
        
        mock_rides = [
            {"row_index": 2, "driver_name": "Mock Driver", "driver_phone": "+123", "pickup_location": "Airport", "scheduled_pickup_time": time_str, "reminder_status": "pending"}
        ]
        
        run_scheduler_cycle()
        assert mock_rides[0]["reminder_status"] == "sent"
        
        # Test 3 - Duplicate Prevention
        print("\nTest 3 - Duplicate Prevention")
        # Run again, status is 'sent', should skip
        run_scheduler_cycle()
        # Ensure it skipped implicitly by observing logs (0 eligible rides)
        
        # Test 4 - Multiple Rides
        print("\nTest 4 - Multiple Rides")
        future_time = datetime.now(tz) + timedelta(minutes=60)
        past_time = datetime.now(tz) - timedelta(minutes=60)
        
        mock_rides = [
            # Future
            {"row_index": 3, "scheduled_pickup_time": future_time.strftime("%Y-%m-%d %H:%M:%S"), "reminder_status": "pending"},
            # Past
            {"row_index": 4, "scheduled_pickup_time": past_time.strftime("%Y-%m-%d %H:%M:%S"), "reminder_status": "pending"},
            # Sent
            {"row_index": 5, "scheduled_pickup_time": time_str, "reminder_status": "sent"},
            # Eligible
            {"row_index": 6, "driver_phone": "+456", "scheduled_pickup_time": time_str, "reminder_status": "pending"},
            # Invalid
            {"row_index": 7, "scheduled_pickup_time": "invalid", "reminder_status": "pending"},
        ]
        
        run_scheduler_cycle()
        assert mock_rides[0]["reminder_status"] == "pending"
        assert mock_rides[1]["reminder_status"] == "pending"
        assert mock_rides[2]["reminder_status"] == "sent"
        assert mock_rides[3]["reminder_status"] == "sent" # Updated by scheduler
        assert mock_rides[4]["reminder_status"] == "pending"
        
        # Test 5 - Twilio Failure
        print("\nTest 5 - Twilio Failure")
        mock_rides = [
            {"row_index": 8, "driver_phone": "+789", "scheduled_pickup_time": time_str, "reminder_status": "pending"}
        ]
        with mock.patch("app.scheduler.make_call", return_value=None):
            run_scheduler_cycle()
            assert mock_rides[0]["reminder_status"] == "pending"
            
    # Test 6 - Google Sheet Failure
    print("\nTest 6 - Google Sheet Failure")
    with mock.patch("app.scheduler.get_rides", side_effect=Exception("API Error")):
        run_scheduler_cycle() # Should not crash, just log and return
        
    print("\nAll deterministic tests completed successfully.")

if __name__ == "__main__":
    test_scheduler_mock_flows()
