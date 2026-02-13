from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import math
from typing import List, Optional

from .database import get_db, UsageLog, init_db
from .schemas import AnalyticsResponse, UserDetailsResponse, UserAnalytics, UsageStats

app = FastAPI(title="Internet Usage Monitoring Service")

@app.on_event("startup")
def startup_event():
    init_db()

def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h{m:02d}m"

def format_size(kb: float) -> str:
    if kb >= 1024 * 1024:
        return f"{kb / (1024 * 1024):.2f}GB"
    elif kb >= 1024:
        return f"{kb / 1024:.2f}MB"
    return f"{kb:.2f}KB"

@app.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    date: str = Query(..., description="DDMMYYYY"),
    pageSize: int = 100,
    page: int = 1,
    db: Session = Depends(get_db)
):
    try:
        target_date = datetime.strptime(date, "%d%m%Y")
    except ValueError:
        return JSONResponse(status_code=422, content={"ok": False, "error": {"message": "invalid date"}})

    if target_date > datetime.now():
        return JSONResponse(status_code=422, content={"ok": False, "error": {"message": "invalid date"}})

    # Time boundaries
    day_1 = target_date - timedelta(days=1)
    day_7 = target_date - timedelta(days=7)
    day_30 = target_date - timedelta(days=30)

    # Subqueries for sums
    def get_usage_for_period(start_date, end_date):
        return db.query(
            UsageLog.username,
            func.sum(UsageLog.usage_time_seconds).label("total_seconds")
        ).filter(
            UsageLog.start_time >= start_date,
            UsageLog.start_time < end_date
        ).group_by(UsageLog.username).subquery()

    usage_30 = get_usage_for_period(day_30, target_date + timedelta(days=1))
    usage_7 = get_usage_for_period(day_7, target_date + timedelta(days=1))
    usage_1 = get_usage_for_period(target_date, target_date + timedelta(days=1))

    # Main query: Top users by usage in last 30 days
    query = db.query(
        UsageLog.username,
        func.coalesce(usage_1.c.total_seconds, 0).label("s1"),
        func.coalesce(usage_7.c.total_seconds, 0).label("s7"),
        func.coalesce(usage_30.c.total_seconds, 0).label("s30")
    ).outerjoin(usage_1, UsageLog.username == usage_1.c.username)\
     .outerjoin(usage_7, UsageLog.username == usage_7.c.username)\
     .outerjoin(usage_30, UsageLog.username == usage_30.c.username)\
     .group_by(UsageLog.username)\
     .order_by(func.coalesce(usage_30.c.total_seconds, 0).desc())

    total_records = query.count()
    total_pages = math.ceil(total_records / pageSize) if total_records > 0 else 0
    results = query.offset((page - 1) * pageSize).limit(pageSize).all()

    data = [
        UserAnalytics(
            username=r.username,
            lastDayUsage=format_duration(r.s1),
            last7DayUsage=format_duration(r.s7),
            last30DayUsage=format_duration(r.s30)
        ) for r in results
    ]

    return {
        "ok": True,
        "data": data,
        "pageSize": pageSize,
        "page": page,
        "totalPages": total_pages
    }

@app.get("/user/search", response_model=UserDetailsResponse)
def search_user(
    username: str,
    datetime_str: str = Query(..., alias="datetime", description="YYYYMMDDThhmm"),
    db: Session = Depends(get_db)
):
    try:
        ref_time = datetime.strptime(datetime_str, "%Y%m%dT%H%M")
    except ValueError:
        return JSONResponse(status_code=400, content={"ok": False, "error": {"message": "invalid datetime format"}})

    def get_stats(hours):
        start = ref_time - timedelta(hours=hours)
        res = db.query(
            func.sum(UsageLog.usage_time_seconds),
            func.sum(UsageLog.upload_kb),
            func.sum(UsageLog.download_kb)
        ).filter(
            UsageLog.username == username,
            UsageLog.start_time >= start,
            UsageLog.start_time <= ref_time
        ).first()
        return res or (0, 0, 0)

    # Check if user exists at all
    exists = db.query(UsageLog).filter(UsageLog.username == username).first()
    if not exists:
        return JSONResponse(status_code=404, content={"ok": False, "error": {"message": "user not found"}})

    h1 = get_stats(1)
    h6 = get_stats(6)
    h24 = get_stats(24)

    return {
        "ok": True,
        "data": {
            "username": username,
            "lastHourUsage": UsageStats(time=format_duration(h1[0] or 0), upload=format_size(h1[1] or 0), download=format_size(h1[2] or 0)),
            "last6HourUsage": UsageStats(time=format_duration(h6[0] or 0), upload=format_size(h6[1] or 0), download=format_size(h6[2] or 0)),
            "last24HourUsage": UsageStats(time=format_duration(h24[0] or 0), upload=format_size(h24[1] or 0), download=format_size(h24[2] or 0))
        }
    }
