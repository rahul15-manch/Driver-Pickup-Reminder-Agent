import time
import threading
import schedule
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from typing import Annotated
import uvicorn
from app.sheets import find_ride_by_call_sid, update_call_status

# 1. Simple logging setup
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# 3. Dummy reminder job
def reminder_job():
    logger.info("Scheduler running: Checking for rides...")

# 4. Background scheduler loop
def run_scheduler():
    # For testing, let's just log every 10 seconds. In production, this can be 1 minute.
    schedule.every(10).seconds.do(reminder_job)
    while True:
        schedule.run_pending()
        time.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting background scheduler thread")
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    yield

# 2. FastAPI app setup (Needed later for Twilio Webhook)
app = FastAPI(title="Driver Pickup Reminder Agent", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"status": "Agent is running", "message": "FastAPI is active and scheduler is running in the background."}

@app.post("/twilio/status")
async def twilio_status(
    CallSid: Annotated[str | None, Form()] = None,
    CallStatus: Annotated[str | None, Form()] = None
):
    """Webhook to receive call status updates from Twilio."""
    if not CallSid:
        logger.warning("Received webhook without CallSid. Ignoring.")
        return {"status": "ignored", "reason": "missing CallSid"}
        
    if not CallStatus:
        logger.warning(f"Received webhook without CallStatus for CallSid {CallSid}. Ignoring.")
        return {"status": "ignored", "reason": "missing CallStatus"}
        
    logger.info(f"Webhook received: CallSid={CallSid}, CallStatus={CallStatus}")
    
    ride = find_ride_by_call_sid(CallSid)
    if not ride:
        logger.warning(f"No ride found for Call SID {CallSid}")
        return {"status": "success", "message": "Call SID not found in sheet"}
        
    row_index = ride.get("row_index")
    success = update_call_status(row_index, CallStatus)
    
    if success:
        logger.info(f"Successfully updated call_status to '{CallStatus}' for row {row_index}")
        return {"status": "success"}
    else:
        logger.error(f"Failed to update call_status to '{CallStatus}' for row {row_index}")
        return {"status": "error", "message": "Failed to update Google Sheet"}

if __name__ == "__main__":
    logger.info("Starting Agent...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
