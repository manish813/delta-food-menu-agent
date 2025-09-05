from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import date

from src.utils.utils import to_camel


class DigitalMenuItemDietaryAsgmt(BaseModel):
    """Menu item dietary assignment"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_item_dietary_code: Optional[str] = None
    menu_item_dietary_desc: Optional[str] = Field(None, examples=["Vegetarian", "Gluten-free", "Dairy-free", "Nut-free"])


class MenuServicePreferences(BaseModel):
    """Menu service preferences"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_service_preference_code: Optional[str] = None
    menu_service_preference_desc: Optional[str] = None
    menu_service_preference_addl_desc: Optional[str] = None


class MenuItem(BaseModel):
    """Individual menu item with details"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_item_id: Optional[int] = None
    product_id: Optional[str] = None
    menu_rrd_product_id: Optional[str] = None
    menu_item_type_cd: Optional[str] = None
    menu_item_type_name: Optional[str] = Field(None, examples=["Bread", "Appetizer", "Main Course", "Wines"])
    menu_item_type_disp_ord_seq_num: Optional[int] = None
    menu_item_disp_ord_seq_num: Optional[int] = None
    menu_item_desc: Optional[str] = None
    menu_item_additional_desc: Optional[str] = None
    menu_item_offer_type_code: Optional[str] = None
    menu_item_offer_type_desc: Optional[str] = None
    menu_item_offer_info: Optional[str] = None
    menu_item_image_url_addr: Optional[str] = None
    menu_item_dietary_asgmts: List[DigitalMenuItemDietaryAsgmt] = Field(default_factory=list)
    menu_item_notes_text: Optional[str] = None
    ssr_code: Optional[str] = Field(None, description="Special Service Request code")
    pre_select_meal: Optional[bool] = Field(None, description="Whether meal can be pre-selected")
    paxia_recipe_spec_code: Optional[str] = None
    menu_item_effective_date: Optional[str] = None
    menu_item_expiry_date: Optional[str] = None




class Menu(BaseModel):
    """Individual menu within a cabin (e.g., Lunch, Dinner, Snacks, Beverages)"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_id: Optional[int] = None
    menu_course_type_code: Optional[str] = None
    menu_course_type_desc: Optional[str] = Field(None, examples=["Meal", "Snacks", "Beverages"])
    menu_service_type_code: Optional[str] = None
    menu_service_type_desc: Optional[str] = Field(None, examples=["LATE", "Breakfast", "Lunch", "Dinner", "Brunch", "Alcoholic Beverages",
                                                                  "Non Alcoholic Beverages", "Pre-Arrival", "Complimentary Snacks",
                                                                  "Complimentary Premium Snacks", "Complimentary Premium Snack Basket",
                                                                  "Mid-Flight Snacks", "All day snacks", "Light Snacks", "Late Night",
                                                                  "Lunch/Dinner", "Dessert", "Beer", "Spirits", "Beverages", "Wines", "Starters",
                                                                  "Beverages Old", "Settling In", "Snacks", "Dinner support", "Pre Arrival AM",
                                                                  "AM Pre-Arrival", "PM Pre-Arrival", "First Service PM Support",
                                                                  "First Service Late Night Support", "Premium Snacks", "First Service AM",
                                                                  "First Service PM", "Pre Arrival PM", "First Service Late Night",
                                                                  "Pre Arrival Lighter/Later", "Mid Flight"])
    menu_type_code: Optional[str] = None
    menu_type_desc: Optional[str] = Field(None, examples=["Western Menu", "Japanese Menu", "Chinese Menu", "Korean Menu", "Skip Meal",])
    menu_type_disp_ord_seq_num: Optional[int] = None
    menu_title_text: Optional[str] = None
    menu_sub_title_text: Optional[str] = None
    menu_disp_ord_seq_num: Optional[int] = None
    menu_notes_text: Optional[str] = None
    menu_manager_name: Optional[str] = None
    menu_image_url_addr: Optional[str] = None
    menu_effective_date: Optional[str] = None
    menu_expiry_date: Optional[str] = None
    pre_select: Optional[str] = None
    paxia_menu_spec_code: List[str] = Field(default_factory=list)
    menu_service_preferences: List[MenuServicePreferences] = Field(default_factory=list)
    menu_items: List[MenuItem] = Field(default_factory=list)


class MenuServiceLanguage(BaseModel):
    """Language details for a menu service"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_service_lang_code: str = Field(..., examples=["EN", "ES", "FR"])
    menu_service_lang_desc: str
    menu_service_lang_selected: bool


class MenuService(BaseModel):
    """Service-level data for a specific cabin class, containing multiple menus"""
    model_config = ConfigDict(alias_generator=to_camel)
    menu_service_id: Optional[int] = None
    menu_service_desc: Optional[str] = None
    cabin_type_code: Optional[str] = Field(None, description="C=Delta One/Business, F=Delta Premium Select/First, W=IMC/Comfort, Y=IMC/Coach")
    cabin_type_desc: Optional[str] = Field(None, examples=["Delta One", "Delta Premium Select", "Main Cabin"])
    menu_planner_name: Optional[str] = None
    cabin_preselect_window_start_utc_ts: Optional[str] = None
    cabin_preselect_window_end_utc_ts: Optional[str] = None
    digital_menu_avl: Optional[bool] = Field(None, description="Whether digital menu is available")
    menu_service_meal_time_window: Optional[str] = Field(None, description="When meal service occurs during flight")
    cabin_welcome_header: Optional[str] = None
    cabin_welcome_title: Optional[str] = None
    cabin_welcome_message: Optional[str] = None
    primary_menu_service_type_desc: Optional[str] = None
    menu_service_languages: Optional[List[MenuServiceLanguage]] = None
    menus: List[Menu] = Field(default_factory=list)


class FlightMenuResponse(BaseModel):
    """Complete flight menu response"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    operating_carrier_code: str = Field(..., examples=["DL"])
    flight_num: int
    flight_departure_date: str = Field(..., examples=["2025-08-13"])
    flight_departure_airport_code: str = Field(..., examples=["ATL", "LAX", "JFK"])
    flight_arrival_date: Optional[str] = Field(None, description="Format: YYYY-MM-DD", examples=["2025-08-13"])
    flight_arrival_airport_code: Optional[str] = Field(None, examples=["ATL", "LAX", "JFK"])
    segment_id: Optional[str] = None
    flight_offer_expiration_utc_ts: Optional[str] = None
    menu_services: List[MenuService] = Field(default_factory=list, description="Menu services by cabin class")
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
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    operating_carrier_code: str
    flight_num: int
    flight_departure_airport_code: str = Field(..., examples=["ATL", "LAX", "JFK"])
    departure_local_date: str = Field(..., description="Format: YYYY-MM-DD", examples=["2025-08-13"])

class CabinAvailability(BaseModel):
    """Menu availability for a specific cabin class"""
    model_config = ConfigDict(alias_generator=to_camel)
    cabin_type_code: Optional[str] = Field(None, description="C=Delta One/Business, F=Delta Premium Select/First, W=IMC/Comfort, Y=IMC/Coach")
    cabin_type_desc: Optional[str] = Field(None, examples=["Delta One", "Delta Premium Select", "IMC"])
    pre_select_menu_available: Optional[bool] = None
    digital_menu_available: Optional[bool] = Field(None, description="Whether digital menu is available via API")
    cabin_preselect_window_start_utc_ts: Optional[str] = None
    cabin_preselect_window_end_utc_ts: Optional[str] = None


class FlightMenuAvailability(BaseModel):
    """Menu availability response for a specific flight"""
    operating_carrier_code: Optional[str] = None
    flight_num: Optional[int] = None
    flight_departure_airport_code: Optional[str] = Field(None, examples=["ATL", "LAX", "JFK"])
    departure_local_date: Optional[str] = Field(None, description="Format: YYYY-MM-DD", examples=["2025-08-13"])
    status: Optional[str] = None
    cabins: Optional[List[CabinAvailability]] = None


class MenuAvailabilityResponse(BaseModel):
    """Complete menu availability response"""
    flight_legs: List[FlightMenuAvailability] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    api_response_time_ms: Optional[int] = None