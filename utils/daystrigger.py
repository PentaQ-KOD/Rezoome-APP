from fastapi import FastAPI
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# สร้าง FastAPI app
app = FastAPI()
scheduler = AsyncIOScheduler()

# ตั้ง trigger ให้รันทุกวันที่ 1 ของเดือนตอน 00:00
monthlyTrigger = CronTrigger(day=1, hour=0, minute=0)
# ตั้ง trigger ให้รันทุกวันตอน 23:59
dailyTrigger = CronTrigger(day_of_week="mon-sun", hour=23, minute=59, second=0)

async def async_reset_key_in_collection():
    """
    This function resets keys in a collection.
    Replace the content with the actual implementation.
    """
    print("[LOG]: Resetting keys in the collection...")

@app.on_event("startup")
async def startup_event():
    """
    เริ่ม Scheduler เมื่อ FastAPI ทำงาน
    """
    scheduler.start()
    print("[LOG]: Scheduler started!")

@app.on_event("shutdown")
async def shutdown_event():
    """
    หยุด Scheduler เมื่อ FastAPI หยุดทำงาน
    """
    scheduler.shutdown()
    print("[LOG]: Scheduler stopped!")

@scheduler.scheduled_job(monthlyTrigger)
async def scheduled_reset_task():
        await async_reset_key_in_collection()
    
@app.get("/status")
async def get_status():
    """
    Endpoint สำหรับตรวจสอบสถานะของ Scheduler
    """
    return {"status": "Scheduler is running" if scheduler.running else "Scheduler is stopped"}