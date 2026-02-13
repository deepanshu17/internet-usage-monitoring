from pydantic import BaseModel
from typing import List, Optional

class UserAnalytics(BaseModel):
    username: str
    lastDayUsage: str
    last7DayUsage: str
    last30DayUsage: str

class AnalyticsResponse(BaseModel):
    ok: bool
    data: List[UserAnalytics]
    pageSize: int
    page: int
    totalPages: int

class UsageStats(BaseModel):
    time: str
    upload: str
    download: str

class UserDetailsData(BaseModel):
    username: str
    lastHourUsage: UsageStats
    last6HourUsage: UsageStats
    last24HourUsage: UsageStats

class UserDetailsResponse(BaseModel):
    ok: bool
    data: UserDetailsData
