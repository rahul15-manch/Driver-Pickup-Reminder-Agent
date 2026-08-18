import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    TEST_PHONE_NUMBER
)

logger = logging.getLogger(__name__)

def get_twilio_client():
    """Initializes and returns the Twilio Client."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.error("Missing Twilio credentials (TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN).")
        return None
    try:
        return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")
        return None

def make_test_call(phone_number: str) -> str | None:
    """
    Initiates an outbound test call playing a static TTS message.
    
    Args:
        phone_number (str): The destination phone number in E.164 format.
        
    Returns:
        str | None: The Call SID if successful, None otherwise.
    """
    if not phone_number:
        logger.error("Phone number is required to make a call.")
        return None
        
    if not TWILIO_PHONE_NUMBER:
        logger.error("TWILIO_PHONE_NUMBER is missing from configuration.")
        return None

    client = get_twilio_client()
    if not client:
        return None

    twiml_message = """
        <Response>
            <Say>
                Hello. This is a test call from the Driver Pickup Reminder Agent.
                This is a pickup reminder.
                Please contact the customer to confirm the pickup
                and make sure you reach the pickup location on time.
                Thank you.
            </Say>
        </Response>
    """
    
    try:
        logger.info(f"Creating test call to {phone_number}...")
        
        # Note: Twilio Trial Accounts often block the inline `twiml` parameter on calls.create
        # with "Invalid or disallowed parameters provided - trial accounts have limited parameter access".
        # We use Twilio's official Twimlets Echo service to pass the TwiML via URL instead.
        from urllib.parse import quote
        twimlet_url = f"http://twimlets.com/echo?Twiml={quote(twiml_message)}"
        
        call = client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twimlet_url
        )
        logger.info(f"Test call created successfully. Call SID: {call.sid}")
        return call.sid
    except TwilioRestException as e:
        logger.error(f"Twilio API Error during call creation: {e.msg}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating call: {e}")
        return None

if __name__ == "__main__":
    # Setup basic console logging for the test
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    print("--- Running Twilio Voice Integration Test ---")
    if not TEST_PHONE_NUMBER:
        logger.error("TEST_PHONE_NUMBER is not configured in .env.")
        print("Please configure TEST_PHONE_NUMBER (E.164 format, e.g., +1234567890) and run the test again.")
    else:
        sid = make_test_call(TEST_PHONE_NUMBER)
        if sid:
            print("\nSUCCESS: Twilio outbound call was initiated.")
            print(f"Call SID: {sid}")
            print("Please verify if the physical test phone rang and the TTS message played.")
        else:
            print("\nFAILURE: Failed to initiate Twilio call. Check logs above.")
