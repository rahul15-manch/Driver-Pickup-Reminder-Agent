import logging
from typing import List, Dict
from app.time_utils import get_minutes_until_pickup

logger = logging.getLogger(__name__)

def find_eligible_rides(rides: List[dict]) -> List[dict]:
    """
    Identifies rides that are eligible for a 30-minute pickup reminder.
    
    Eligibility rules:
    - minutes_until_pickup is between 29 and 30 inclusive.
    - reminder_status is NOT 'sent'.
    
    Args:
        rides (List[dict]): List of ride dictionaries from Google Sheets.
        
    Returns:
        List[dict]: List of rides that require a reminder.
    """
    eligible_rides = []
    
    for ride in rides:
        try:
            # 1. Get scheduled pickup time
            pickup_time = ride.get("scheduled_pickup_time")
            if not pickup_time:
                continue
            
            # 2. Get minutes until pickup
            minutes_until = get_minutes_until_pickup(pickup_time)
            if minutes_until is None:
                continue
                
            # 3. Check 30-minute window (29-30 mins) - updated to 0-30 for testing
            is_in_time_window = 0 <= minutes_until <= 30
            
            # 4. Check reminder status
            # Treat empty/missing as 'pending'
            status = str(ride.get("reminder_status", "")).strip().lower()
            already_sent = (status == "sent")
            
            # 5. Evaluate eligibility
            if is_in_time_window and not already_sent:
                logger.info(f"Ride #{ride.get('row_index', 'Unknown')} is {minutes_until} minutes away — ELIGIBLE")
                eligible_rides.append(ride)
            else:
                # Optional: Log skips for testing/debugging, but limit noise in production
                # logger.debug(f"Ride #{ride.get('row_index', 'Unknown')} skipped (Minutes: {minutes_until}, Status: {status})")
                pass
                
        except Exception as e:
            logger.error(f"Error evaluating ride #{ride.get('row_index', 'Unknown')}: {e}")
            
    return eligible_rides
