import time
import logging
from app.sheets import get_rides, mark_reminder_sent
from app.trigger import find_eligible_rides
from app.reminder import build_reminder_message
from app.twilio_service import make_call
import app.config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def run_scheduler_cycle():
    """Performs a single cycle of checking rides and making calls."""
    logger.info("Checking scheduled rides...")
    
    try:
        rides = get_rides()
    except Exception as e:
        logger.error(f"Failed to retrieve rides: {e}")
        return

    num_rides = len(rides) if rides else 0
    logger.info(f"Found {num_rides} rides")
    
    if num_rides == 0:
        logger.info("No eligible rides")
        return

    try:
        eligible_rides = find_eligible_rides(rides)
    except Exception as e:
        logger.error(f"Failed to find eligible rides: {e}")
        return

    num_eligible = len(eligible_rides) if eligible_rides else 0
    if num_eligible == 0:
        logger.info("Found 0 eligible rides")
        return
        
    logger.info(f"Found {num_eligible} eligible ride(s)")

    for ride in eligible_rides:
        row_index = ride.get("row_index")
        driver_name = ride.get("driver_name", "Driver")
        driver_phone = ride.get("driver_phone")
        
        logger.info(f"Ride #{row_index} is eligible")
        logger.info(f"Driver: {driver_name}")
        logger.info(f"Pickup: {ride.get('pickup_location', 'Unknown')}")
        
        if not driver_phone:
            logger.warning(f"No phone number found for ride #{row_index}. Skipping.")
            continue
            
        logger.info("Generating reminder")
        try:
            message = build_reminder_message(ride)
        except Exception as e:
            logger.error(f"Failed to generate reminder for ride #{row_index}: {e}")
            continue

        logger.info("Calling driver")
        call_sid = make_call(driver_phone, message)
        
        if call_sid:
            logger.info(f"Call created: {call_sid}")
            logger.info("Marking reminder as sent")
            success = mark_reminder_sent(row_index, call_sid)
            if success:
                logger.info(f"Ride #{row_index} reminder recorded")
            else:
                logger.error(f"Failed to record reminder sent for ride #{row_index}")
        else:
            logger.warning(f"Reminder call failed for ride #{row_index}")
            logger.warning("Ride remains pending")


def start_scheduler():
    """Starts the endless polling loop."""
    logger.info("Driver Pickup Reminder Agent started")
    logger.info("Scheduler interval: 60 seconds")
    logger.info(f"Timezone: {app.config.TIMEZONE}")
    
    try:
        while True:
            run_scheduler_cycle()
            logger.info("Waiting 60 seconds")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler")
        
if __name__ == "__main__":
    start_scheduler()
