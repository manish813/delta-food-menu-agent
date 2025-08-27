from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, Dict, Any, List


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


class ValidationParameters(BaseModel):
    """Parameters used in validation"""
    flight_departure_date: str
    flight_number: int
    flight_departure_airport: str
    operating_carrier: str


class ValidationNextSteps(BaseModel):
    """Next steps based on validation result"""
    valid: str = "Ready to make API call"
    invalid: str = "Please fix the issues above before proceeding"


class FlightRequestValidation(BaseModel):
    """Validation response for flight request parameters"""
    tool: str = "request_validation"
    is_valid: bool
    issues: List[str]
    recommendations: List[str]
    parameters: ValidationParameters
    next_steps: ValidationNextSteps


class DebugRequest(BaseModel):
    """Request for debugging API calls"""
    endpoint: str = Field(default="menuByFlight")
    params: dict = Field(default_factory=dict)
    include_raw_response: bool = Field(default=False)