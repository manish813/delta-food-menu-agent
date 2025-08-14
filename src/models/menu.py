from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date


class MenuItem(BaseModel):
    """Individual menu item with details"""
    name: str = Field(..., description="Name of the menu item")
    description: Optional[str] = None
    category: str  # appetizer, entree, dessert, beverage, etc.
    dietary_info: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None


class CabinMenu(BaseModel):
    """Menu for a specific cabin class"""
    cabin_code: str = Field(..., description="Cabin class code (F, C, Y)")
    cabin_name: str = Field(..., description="Name of the cabin class (e.g., First, Business, Economy)") 
    menu_items: List[MenuItem] = Field(default_factory=list)
    service_time: Optional[str] = None
    special_notes: Optional[str] = None


class FlightMenuResponse(BaseModel):
    """Complete flight menu response"""
    carrier_code: str = Field(..., description="Airline carrier code")
    flight_number: int = Field(..., description="Flight number")
    departure_date: date = Field(..., description="Date of the flight departure")
    departure_airport: str = Field(..., description="Departure airport code")
    arrival_airport: Optional[str] = None
    cabins: List[CabinMenu] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    api_response_time_ms: Optional[int] = None


class FlightMenuError(BaseModel):
    """Error response structure"""
    success: bool = False
    error_message: str
    error_code: Optional[str] = None
    request_params: Optional[Dict] = None


class CabinAvailability(BaseModel):
    """Menu availability for a specific cabin class"""
    cabin_type_code: str = Field(..., description="Cabin class code (C, F, W, Y)")
    cabin_type_desc: str = Field(..., description="Name of the cabin class (e.g., Business, First)")
    pre_select_menu_available: bool = Field(..., description="Whether pre-select menu is available")
    digital_menu_available: bool = Field(..., description="Whether digital menu is available via our API")
    cabin_preselect_window_start_utc_ts: Optional[str] = Field(None, description="Pre-select window start time in UTC")
    cabin_preselect_window_end_utc_ts: Optional[str] = Field(None, description="Pre-select window end time in UTC")


class FlightMenuAvailability(BaseModel):
    """Menu availability response for a specific flight"""
    operating_carrier_code: str = Field(..., description="Airline carrier code")
    flight_num: int = Field(..., description="Flight number")
    flight_departure_airport_code: str = Field(..., description="Departure airport code")
    departure_local_date: str = Field(..., description="Flight departure date")
    status: str = Field(..., description="API response status")
    cabins: List[CabinAvailability] = Field(..., description="Availability info for each cabin class")


class MenuAvailabilityResponse(BaseModel):
    """Complete menu availability response"""
    flight_legs: List[FlightMenuAvailability] = Field(..., description="Availability for all requested flights")
    success: bool = True
    error_message: Optional[str] = None
    api_response_time_ms: Optional[int] = None