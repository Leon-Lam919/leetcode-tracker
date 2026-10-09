from fastapi import APIRouter, HTTPException

from config import settings
from services import notify

router = APIRouter()


@router.post("/notify/test")
def send_test_notification():
    """Send a test notification, to check your phone setup."""
    if not settings.ntfy_topic:
        raise HTTPException(status_code=400, detail="NTFY_TOPIC is not set in .env")
    try:
        notify.send("LeetCode Tracker test", "Notifications work. 🎉")
    except notify.NotifyError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {"sent": True}
