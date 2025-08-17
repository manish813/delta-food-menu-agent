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


class Menu(BaseModel):
    """Individual menu within a cabin (e.g., Lunch, Dinner, Snacks, Beverages)"""
    menu_id: Optional[str] = None
    course_type: Optional[str] = Field(None, description="Course type like 'Meal', 'Snacks', 'Beverages'")
    service_type: Optional[str] = Field(None, description="Service type like 'Lunch/Dinner', 'Light Bites', 'Wines'")
    menu_type: Optional[str] = Field(None, description="Menu type like 'Western Menu'")
    title: Optional[str] = Field(None, description="Menu title text")
    subtitle: Optional[str] = Field(None, description="Menu subtitle text")
    menu_items: List[MenuItem] = Field(default_factory=list)
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None


class MenuServiceLanguage(BaseModel):
    """Language details for a menu service"""
    menu_service_lang_code: str = Field(..., description="Language code")
    menu_service_lang_desc: str = Field(..., description="Language description")
    menu_service_lang_selected: bool = Field(..., description="Indicates if the language is selected")


class MenuService(BaseModel):
    """Service-level data for a specific cabin class, containing multiple menus"""
    menu_service_id: int = Field(..., description="Unique identifier for the menu service")
    menu_service_desc: str = Field(..., description="Description of the menu service")
    menu_service_meal_time_window: str = Field(..., description="Meal time window description")
    cabin_type_code: str = Field(..., description="Cabin class code (C, F, W, Y)")
    cabin_type_desc: str = Field(..., description="Name of the cabin class (e.g., Delta One)")
    cabin_welcome_header: str = Field(..., description="Welcome header text")
    cabin_welcome_title: str = Field(..., description="Welcome title text")
    cabin_welcome_message: str = Field(..., description="Welcome message text")
    primary_menu_service_type_desc: str = Field(..., description="Primary service type description")
    menu_service_languages: List[MenuServiceLanguage] = Field(..., description="List of available languages")
    menus: List[Menu] = Field(default_factory=list)


class FlightMenuResponse(BaseModel):
    """Complete flight menu response"""
    carrier_code: str = Field(..., description="Airline carrier code")
    flight_number: int = Field(..., description="Flight number")
    departure_date: date = Field(..., description="Date of the flight departure")
    departure_airport: str = Field(..., description="Departure airport code")
    arrival_airport: Optional[str] = None
    menu_services: List[MenuService] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    api_response_time_ms: Optional[int] = None


class FlightMenuError(BaseModel):
    """Error response structure"""
    success: bool = False
    error_message: str
    error_code: Optional[str] = None
    request_params: Optional[Dict] = None

class FlightLeg(BaseModel):
    """Details of a flight leg for menu availability"""
    operating_carrier_code: str = Field(..., description="Airline carrier code")
    flight_num: int = Field(..., description="Flight number")
    flight_departure_airport_code: str = Field(..., description="Departure airport code")
    departure_local_date: str = Field(..., description="Flight departure date in local timezone")

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