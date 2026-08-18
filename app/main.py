import time
import threading
import schedule
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

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

if __name__ == "__main__":
    logger.info("Starting Agent...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
