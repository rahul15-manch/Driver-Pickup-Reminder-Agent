import logging
from datetime import datetime
import pytz
from app.config import TIMEZONE

logger = logging.getLogger(__name__)

def get_minutes_until_pickup(scheduled_pickup_time: str) -> int | None:
    """
    Parses the scheduled pickup time and calculates the minutes remaining 
    until pickup in the configured timezone.

    Expected format: YYYY-MM-DD HH:MM:SS (e.g., "2026-08-19 10:30:00")
    
    Returns:
        int: Minutes remaining (positive for future, negative for past)
        None: If timestamp is invalid or missing
    """
    if not scheduled_pickup_time:
        logger.warning("Missing pickup time.")
        return None

    try:
        # Load the timezone (default Asia/Kolkata)
        tz = pytz.timezone(TIMEZONE)
        
        # Parse the string into a naive datetime
        naive_dt = datetime.strptime(scheduled_pickup_time.strip(), "%Y-%m-%d %H:%M:%S")
        
        # Localize the naive datetime to make it timezone-aware
        pickup_dt = tz.localize(naive_dt)
        
        # Get the current time in the same timezone
        now_dt = datetime.now(tz)
        
        # Calculate the difference
        time_difference = pickup_dt - now_dt
        
        # Convert the difference to total minutes (rounded down to nearest whole minute)
        minutes_until = int(time_difference.total_seconds() // 60)
        
        return minutes_until

    except ValueError as e:
        logger.error(f"Invalid timestamp format '{scheduled_pickup_time}'. Expected YYYY-MM-DD HH:MM:SS. Error: {e}")
        return None
    except pytz.UnknownTimeZoneError:
        logger.error(f"Invalid timezone configured: {TIMEZONE}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing time: {e}")
        return None
