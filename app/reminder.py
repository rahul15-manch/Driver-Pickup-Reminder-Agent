import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def build_reminder_message(ride: dict) -> str:
    """
    Generates a clear, personalized voice reminder from a ride dictionary.
    
    Args:
        ride (dict): The ride data extracted from Google Sheets.
        
    Returns:
        str: The plain text reminder message.
    """
    # 1. Driver Name (Fallback: Driver)
    driver_name = ride.get("driver_name")
    if not driver_name or str(driver_name).strip() == "":
        driver_name = "Driver"
    else:
        driver_name = str(driver_name).strip()
        
    # 2. Pickup Location (Fallback: your scheduled pickup location)
    pickup_location = ride.get("pickup_location")
    if not pickup_location or str(pickup_location).strip() == "":
        pickup_location = "your scheduled pickup location"
    else:
        pickup_location = str(pickup_location).strip()
        
    # 3. Pickup Time formatting
    raw_time = ride.get("scheduled_pickup_time")
    formatted_time = "your scheduled time"
    
    if raw_time and str(raw_time).strip() != "":
        try:
            # Parse the timestamp YYYY-MM-DD HH:MM:SS
            dt = datetime.strptime(str(raw_time).strip(), "%Y-%m-%d %H:%M:%S")
            # Format to human readable (e.g., 10:30 AM)
            # Remove leading zero from hour if present (on Windows %#I works, on Unix %-I works)
            # To be safe cross-platform, we can format and strip left zeroes.
            time_str = dt.strftime("%I:%M %p")
            if time_str.startswith("0"):
                time_str = time_str[1:]
            formatted_time = time_str
        except ValueError as e:
            logger.error(f"Invalid timestamp format while building reminder message: '{raw_time}'. Error: {e}")
            # fallback remains "your scheduled time"
            
    # 4. Generate the complete message
    message = (
        f"Hello {driver_name}. This is your pickup reminder. "
        f"Your scheduled pickup is at {pickup_location} at {formatted_time}. "
        "Please contact the customer to confirm the pickup "
        "and make sure you reach the pickup location on time. Thank you."
    )
    
    return message
