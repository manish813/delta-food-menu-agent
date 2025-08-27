from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class MenuQueryRequest(BaseModel):
    """Request parameters for Delta menu API"""
    departure_date: date = Field(description="Flight departure date (YYYY-MM-DD)")
    flight_number: int = Field(gt=0, description="Flight number")
    departure_airport: str = Field(description="Departure airport code")
    operating_carrier: str = Field(default="DL", description="Airline carrier code")
    lang_cd: str = Field(default="en-US", description="Language code")

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class DebugRequest(BaseModel):
    """Request for debugging API calls"""
    endpoint: str = Field(default="menuByFlight")
    params: dict = Field(default_factory=dict)
    include_raw_response: bool = Field(default=False)