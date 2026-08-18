import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from app.config import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_NAME, TIMEZONE
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# Constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Initializes and returns the Google Sheets API service."""
    if not GOOGLE_CREDENTIALS_FILE or not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        logger.error(f"Missing credentials file at {GOOGLE_CREDENTIALS_FILE}. Check GOOGLE_CREDENTIALS_FILE.")
        return None
    try:
        credentials = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Failed to authenticate with Google Sheets API: {e}")
        return None

def get_rides():
    """Reads rides from Google Sheets and returns them as a list of dictionaries."""
    service = get_sheets_service()
    if not service:
        logger.error("Could not connect to Google Sheets.")
        return []

    if not GOOGLE_SHEET_ID:
        logger.error("Missing GOOGLE_SHEET_ID in environment.")
        return []

    try:
        sheet = service.spreadsheets()
        # Read all rows from the specified sheet
        range_name = f"{GOOGLE_SHEET_NAME}"
        result = sheet.values().get(spreadsheetId=GOOGLE_SHEET_ID, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            logger.info("No data found in the spreadsheet.")
            return []

        # The first row contains the headers
        headers = values[0]
        rides = []

        # Start from the second row (index 1) for the data
        for index, row in enumerate(values[1:], start=2): # 1-based index: headers=1, data starts at 2
            # Zip headers with row safely handles rows shorter than headers
            ride_data = dict(zip(headers, row))
            ride_data['row_index'] = index
            
            # Ensure reminder_status exists in the dict even if it was empty in the sheet
            if 'reminder_status' not in ride_data:
                ride_data['reminder_status'] = ''
                
            rides.append(ride_data)

        logger.info(f"Found {len(rides)} rides from Google Sheets.")
        return rides
    except Exception as e:
        logger.error(f"Failed to fetch rides from Google Sheets: {e}")
        return []

def update_ride_status(row_index, status, column_name="reminder_status"):
    """Updates a specific status column for a specific row in the Google Sheet."""
    service = get_sheets_service()
    if not service or not GOOGLE_SHEET_ID:
        logger.error("Could not connect to Google Sheets.")
        return False
    
    try:
        sheet = service.spreadsheets()
        # Find column index dynamically from headers
        header_result = sheet.values().get(spreadsheetId=GOOGLE_SHEET_ID, range=f"{GOOGLE_SHEET_NAME}!1:1").execute()
        headers = header_result.get('values', [[]])[0]
        
        if column_name not in headers:
            logger.error(f"Column '{column_name}' not found in sheet headers.")
            return False
            
        col_idx = headers.index(column_name)
        # Convert index (0-based) to letter (A, B, C...)
        # Note: This simple conversion works for up to 26 columns (A-Z).
        # We assume the sheet is not wider than 26 columns for this simple version.
        col_letter = chr(65 + col_idx) 
        
        range_to_update = f"{GOOGLE_SHEET_NAME}!{col_letter}{row_index}"
        body = {
            'values': [[status]]
        }
        
        sheet.values().update(
            spreadsheetId=GOOGLE_SHEET_ID, 
            range=range_to_update,
            valueInputOption="USER_ENTERED", 
            body=body
        ).execute()
            
        logger.info(f"Updated {column_name} at row {row_index} to '{status}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to update ride status: {e}")
        return False

def mark_reminder_sent(row_index: int, call_sid: str) -> bool:
    """
    Marks a ride as sent to prevent duplicate calls.
    Updates reminder_status, call_sid, and reminder_sent_at.
    """
    if not row_index or not call_sid:
        logger.error("row_index and call_sid are required to mark reminder as sent.")
        return False
        
    try:
        # Get current time in correct timezone
        tz = pytz.timezone(TIMEZONE)
        sent_at = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        
        # We will reuse the existing update_ride_status sequentially.
        # This makes 3 API calls which is fine for v1 scale.
        status_updated = update_ride_status(row_index, "sent", column_name="reminder_status")
        sid_updated = update_ride_status(row_index, call_sid, column_name="call_sid")
        time_updated = update_ride_status(row_index, sent_at, column_name="reminder_sent_at")
        
        if status_updated and sid_updated and time_updated:
            logger.info(f"Successfully recorded reminder state for row {row_index}")
            return True
        else:
            logger.error(f"Partial update failure when marking row {row_index} as sent.")
            return False
            
    except Exception as e:
        logger.error(f"Failed to record reminder state: {e}")
        return False
