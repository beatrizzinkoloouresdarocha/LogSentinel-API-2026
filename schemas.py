from datetime import datetime
from pydantic import BaseModel, Field


class LogCreate(BaseModel):
    service_name: str = Field(..., example="auth-service")
    level: str = Field(
        ..., example="CRITICAL"
    )  # INFO, WARNING, ERROR, CRITICAL
    message: str = Field(..., example="Database connection failed: timeout")


class LogResponse(LogCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True