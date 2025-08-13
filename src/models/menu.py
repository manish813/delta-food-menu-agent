from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date


class MenuItem(BaseModel):
    """Individual menu item with details"""
    name: str
    description: Optional[str] = None
    category: str  # appetizer, entree, dessert, beverage, etc.
    dietary_info: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None


class CabinMenu(BaseModel):
    """Menu for a specific cabin class"""
    cabin_code: str  # F, C, Y, etc.
    cabin_name: str  # First, Business, Economy
    menu_items: List[MenuItem] = Field(default_factory=list)
    service_time: Optional[str] = None
    special_notes: Optional[str] = None


class FlightMenuResponse(BaseModel):
    """Complete flight menu response"""
    carrier_code: str
    flight_number: int
    departure_date: date
    departure_airport: str
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