from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import date

from src.utils.utils import to_camel


class DigitalMenuItemDietaryAsgmt(BaseModel):
    """Menu item dietary assignment"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_item_dietary_code: Optional[str] = Field(None, description="Menu item dietary code")
    menu_item_dietary_desc: Optional[str] = Field(None, description="Menu item dietary description")


class MenuServicePreferences(BaseModel):
    """Menu service preferences"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_service_preference_code: Optional[str] = Field(None, description="Menu service preference code")
    menu_service_preference_desc: Optional[str] = Field(None, description="Menu service preference description")
    menu_service_preference_addl_desc: Optional[str] = Field(None, description="Additional menu service preference description")


class MenuItem(BaseModel):
    """Individual menu item with details"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_item_id: Optional[int] = Field(None, description="Menu item ID")
    product_id: Optional[str] = Field(None, description="Product ID")
    menu_rrd_product_id: Optional[str] = Field(None, description="Menu RRD product ID")
    menu_item_type_cd: Optional[str] = Field(None, description="Menu item type code")
    menu_item_type_name: Optional[str] = Field(None, description="Menu item type name")
    menu_item_type_disp_ord_seq_num: Optional[int] = Field(None, description="Menu item type display order sequence number")
    menu_item_disp_ord_seq_num: Optional[int] = Field(None, description="Menu item display order sequence number")
    menu_item_desc: Optional[str] = Field(None, description="Menu item description")
    menu_item_additional_desc: Optional[str] = Field(None, description="Menu item additional description")
    menu_item_offer_type_code: Optional[str] = Field(None, description="Menu item offer type code")
    menu_item_offer_type_desc: Optional[str] = Field(None, description="Menu item offer type description")
    menu_item_offer_info: Optional[str] = Field(None, description="Menu item offer information")
    menu_item_image_url_addr: Optional[str] = Field(None, description="Menu item image URL address")
    menu_item_dietary_asgmts: List[DigitalMenuItemDietaryAsgmt] = Field(default_factory=list, description="Menu item dietary assignments")
    menu_item_notes_text: Optional[str] = Field(None, description="Menu item notes text")
    ssr_code: Optional[str] = Field(None, description="SSR code")
    pre_select_meal: Optional[bool] = Field(None, description="Pre-select meal flag")
    paxia_recipe_spec_code: Optional[str] = Field(None, description="PAXIA recipe specification code")
    menu_item_effective_date: Optional[str] = Field(None, description="Menu item effective date")
    menu_item_expiry_date: Optional[str] = Field(None, description="Menu item expiry date")




class Menu(BaseModel):
    """Individual menu within a cabin (e.g., Lunch, Dinner, Snacks, Beverages)"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_id: Optional[int] = None
    menu_course_type_code: Optional[str] = Field(None, description="Menu course type code")
    menu_course_type_desc: Optional[str] = Field(None, description="Course type like 'Meal', 'Snacks', 'Beverages'")
    menu_service_type_code: Optional[str] = Field(None, description="Menu service type code")
    menu_service_type_desc: Optional[str] = Field(None, description="Service type like 'Lunch/Dinner', 'Light Bites', 'Wines'")
    menu_type_code: Optional[str] = Field(None, description="Menu type code")
    menu_type_desc: Optional[str] = Field(None, description="Menu type like 'Western Menu'")
    menu_type_disp_ord_seq_num: Optional[str] = Field(None, description="Menu type display order sequence number")
    menu_title_text: Optional[str] = Field(None, description="Menu title text")
    menu_sub_title_text: Optional[str] = Field(None, description="Menu subtitle text")
    menu_disp_ord_seq_num: Optional[int] = Field(None, description="Menu display order sequence number")
    menu_notes_text: Optional[str] = Field(None, description="Menu notes text")
    menu_manager_name: Optional[str] = Field(None, description="Menu manager name")
    menu_image_url_addr: Optional[str] = Field(None, description="Menu image URL address")
    menu_effective_date: Optional[str] = Field(None, description="Menu effective date")
    menu_expiry_date: Optional[str] = Field(None, description="Menu expiry date")
    pre_select: Optional[str] = Field(None, description="Pre-select option")
    paxia_menu_spec_code: List[str] = Field(default_factory=list, description="PAXIA menu specification codes")
    menu_service_preferences: List[MenuServicePreferences] = Field(default_factory=list, description="Menu service preferences")
    menu_items: List[MenuItem] = Field(default_factory=list)


class MenuServiceLanguage(BaseModel):
    """Language details for a menu service"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_service_lang_code: str = Field(..., description="Language code")
    menu_service_lang_desc: str = Field(..., description="Language description")
    menu_service_lang_selected: bool = Field(..., description="Indicates if the language is selected")


class MenuService(BaseModel):
    """Service-level data for a specific cabin class, containing multiple menus"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_service_id: Optional[int] = Field(None, description="Unique identifier for the menu service")
    menu_service_desc: Optional[str] = Field(None, description="Description of the menu service")
    cabin_type_code: Optional[str] = Field(None, description="Cabin class code (C, F, W, Y)")
    cabin_type_desc: Optional[str] = Field(None, description="Name of the cabin class (e.g., Delta One)")
    menu_planner_name: Optional[str] = Field(None, description="Name of the menu planner")
    cabin_preselect_window_start_utc_ts: Optional[str] = Field(None, description="Pre-select window start time in UTC")
    cabin_preselect_window_end_utc_ts: Optional[str] = Field(None, description="Pre-select window end time in UTC")
    digital_menu_avl: Optional[bool] = Field(None, description="Whether digital menu is available")
    menu_service_meal_time_window: Optional[str] = Field(None, description="Meal time window description")
    cabin_welcome_header: Optional[str] = Field(None, description="Welcome header text")
    cabin_welcome_title: Optional[str] = Field(None, description="Welcome title text")
    cabin_welcome_message: Optional[str] = Field(None, description="Welcome message text")
    primary_menu_service_type_desc: Optional[str] = Field(None, description="Primary service type description")
    menu_service_languages: Optional[List[MenuServiceLanguage]] = Field(None, description="List of available languages")
    menus: List[Menu] = Field(default_factory=list)


class FlightMenuResponse(BaseModel):
    """Complete flight menu response"""
    model_config = ConfigDict(alias_generator=to_camel)
    operating_carrier_code: str = Field(..., description="Airline carrier code", examples=["DL"])
    flight_num: int = Field(..., description="Flight number")
    flight_departure_date: str = Field(..., description="Flight departure date")
    flight_departure_airport_code: str = Field(..., description="Flight departure airport code")
    flight_arrival_date: Optional[str] = Field(None, description="Flight arrival date")
    flight_arrival_airport_code: Optional[str] = Field(None, description="Flight arrival airport code")
    segment_id: Optional[str] = Field(None, description="Flight segment identifier")
    flight_offer_expiration_utc_ts: Optional[str] = Field(None, description="Flight offer expiration timestamp in UTC")
    menu_services: List[MenuService] = Field(default_factory=list, description="List of menu services for different cabin classes")
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
    model_config = ConfigDict(alias_generator=to_camel)
    operating_carrier_code: str = Field(..., description="Airline carrier code")
    flight_num: int = Field(..., description="Flight number")
    flight_departure_airport_code: str = Field(..., description="Departure airport code")
    departure_local_date: str = Field(..., description="Flight departure date in local timezone")

class CabinAvailability(BaseModel):
    """Menu availability for a specific cabin class"""
    model_config = ConfigDict(alias_generator=to_camel)
    cabin_type_code: Optional[str] = Field(None, description="Cabin class code (C, F, W, Y)")
    cabin_type_desc: Optional[str] = Field(None, description="Name of the cabin class (e.g., Business, First)")
    pre_select_menu_available: Optional[bool] = Field(None, description="Whether pre-select menu is available")
    digital_menu_available: Optional[bool] = Field(None, description="Whether digital menu is available via our API")
    cabin_preselect_window_start_utc_ts: Optional[str] = Field(None, description="Pre-select window start time in UTC")
    cabin_preselect_window_end_utc_ts: Optional[str] = Field(None, description="Pre-select window end time in UTC")


class FlightMenuAvailability(BaseModel):
    """Menu availability response for a specific flight"""
    operating_carrier_code: Optional[str] = Field(None, description="Airline carrier code")
    flight_num: Optional[int] = Field(None, description="Flight number")
    flight_departure_airport_code: Optional[str] = Field(None, description="Departure airport code")
    departure_local_date: Optional[str] = Field(None, description="Flight departure date")
    status: Optional[str] = Field(None, description="API response status")
    cabins: Optional[List[CabinAvailability]] = Field(None, description="Availability info for each cabin class")


class MenuAvailabilityResponse(BaseModel):
    """Complete menu availability response"""
    flight_legs: List[FlightMenuAvailability] = Field(..., description="Availability for all requested flights")
    success: bool = True
    error_message: Optional[str] = None
    api_response_time_ms: Optional[int] = None