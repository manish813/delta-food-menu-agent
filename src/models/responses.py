from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import date

from src.models.menu import MenuService


class FlightOption(BaseModel):
    flight_number: int
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None


class FlightLookupResponse(BaseModel):
    departure_airport: str
    arrival_airport: str
    departure_date: str
    operating_carrier: str
    flights: List[FlightOption]
    success: bool
    error_message: Optional[str] = None


# Using a simplified MenuItem for tool output
class SimpleMenuItem(BaseModel):
    name: str
    description: Optional[str] = None
    dietary_info: Optional[List[str]] = None

class FlightInfo(BaseModel):
    carrier: str
    flight_number: int
    date: date
    departure_airport: str
    arrival_airport: Optional[str] = None

class ToolResponse(BaseModel):
    query_type: str
    success: bool
    error_message: Optional[str] = None

class CompleteMenuResponse(ToolResponse):
    flight_info: Optional[FlightInfo] = None
    menu_services: Optional[List[MenuService]] = None
    availability_check: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class CabinDetail(BaseModel):
    code: str
    name: str
    service_time: Optional[str] = None
    special_notes: Optional[str] = None

class CabinComparisonDetail(BaseModel):
    name: str
    menu_summary: Dict[str, Any]
    highlights: List[Dict[str, str]]

