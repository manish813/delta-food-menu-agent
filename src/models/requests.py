from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class MenuQueryRequest(BaseModel):
    """Request parameters for Delta menu API"""
    departure_date: date
    flight_number: int
    departure_airport: str = Field(description="Departure airport code")
    operating_carrier: str = Field(default="DL", description="Airline carrier code")
    cabin_code: Optional[str] = Field(default=None, description="Specific cabin class (F, C, Y)")
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