from typing import List, Dict, Any
from datetime import date

from agents import function_tool
from ..client.delta_client import DeltaMenuClient
from ..models.requests import MenuQueryRequest
from ..models.menu import FlightMenuResponse,  FlightLeg
from ..models.responses import (
    CompleteMenuResponse,
    CabinComparisonResponse,
    FlightInfo,
    SimpleMenuItem,
    CabinDetail,
    CabinComparisonDetail,
)


class MenuTools:
    """Tools for querying Delta flight menus"""
    
    def __init__(self, client: DeltaMenuClient):
        self.client = client
    
    @function_tool
    async def get_menu_by_flight(
        self,
        departure_date: str,
        flight_number: int,
        departure_airport: str = "ATL",
        operating_carrier: str = "DL",
        lang_cd: str = "en-US",
        check_availability: bool = False
    ) -> Dict[str, Any]:
        """
        Get complete menu for a specific flight across all cabin classes.
        
        Args:
            departure_date: Flight departure date in YYYY-MM-DD format
            flight_number: Flight number (e.g., 30 for DL30)
            departure_airport: Departure airport code (default: ATL)
            operating_carrier: Airline carrier code (default: DL)
            lang_cd: Language code (default: en-US)
            check_availability: Whether to check menu availability first (default: False)
            
        Returns:
            Structured response with flight info and cabin menus
        """
        try:
            # Optional: Check availability first
            if check_availability:
                flight_leg = FlightLeg(
                    operating_carrier_code=operating_carrier,
                    flight_num=flight_number,
                    flight_departure_airport_code=departure_airport,
                    departure_local_date=departure_date,
                )
                availability_response = await self.client.check_menu_availability(flight_legs=[flight_leg])
                availability = {
                    "success": availability_response.success,
                    "error_message": availability_response.error_message,
                    "availability": {}
                }
                if availability_response.success and availability_response.flight_legs:
                    flight_leg_availability = availability_response.flight_legs[0]
                    availability["availability"] = {
                        cabin.cabin_type_code: cabin.model_dump()
                        for cabin in flight_leg_availability.cabins
                    }
                
                if not availability["success"]:
                    return CompleteMenuResponse(
                        query_type="complete_menu",
                        success=False,
                        error_message=f"Availability check failed: {availability['error_message']}",
                        availability_check=availability
                    ).model_dump(exclude_none=True)
                
                # Check if any cabin has digital menu available
                available_cabins = [
                    code for code, info in availability["availability"].items()
                    if info["digital_menu_available"]
                ]
                
                if not available_cabins:
                    return CompleteMenuResponse(
                        query_type="complete_menu",
                        success=False,
                        error_message="No digital menus available for this flight",
                        availability_check=availability
                    ).model_dump(exclude_none=True)
            
            # Parse date string
            dep_date = date.fromisoformat(departure_date)
            
            # Create request
            request = MenuQueryRequest(
                departure_date=dep_date,
                flight_number=flight_number,
                departure_airport=departure_airport,
                operating_carrier=operating_carrier,
                lang_cd=lang_cd
            )
            
            # Get menu data
            response = await self.client.get_menu_by_flight(request)
            
            # Format response for readability
            flight_info = FlightInfo(
                carrier=response.carrier_code,
                flight_number=response.flight_number,
                date=response.departure_date,
                departure_airport=response.departure_airport,
                arrival_airport=response.arrival_airport
            )

            return CompleteMenuResponse(
                query_type="complete_menu",
                flight_info=flight_info,
                success=response.success,
                error_message=response.error_message,
                menu_services=response.menu_services,
                metadata={"api_response_time_ms": response.api_response_time_ms}
            ).model_dump(exclude_none=True)
            
        except ValueError as e:
            return CompleteMenuResponse(
                query_type="complete_menu",
                success=False,
                error_message=f"Invalid date format: {e}. Use YYYY-MM-DD format."
            ).model_dump(exclude_none=True)
        except Exception as e:
            return CompleteMenuResponse(
                query_type="complete_menu",
                success=False,
                error_message=str(e)
            ).model_dump(exclude_none=True)

    @function_tool
    async def check_menu_availability(
        self,
        departure_date: str,
        flight_number: int,
        departure_airport: str = "ATL",
        operating_carrier: str = "DL",
    ) -> Dict[str, Any]:
        """
        Check menu availability for a specific flight.

        Args:
            departure_date: Flight departure date in YYYY-MM-DD format
            flight_number: Flight number
            departure_airport: Departure airport code (default: ATL)
            operating_carrier: Airline carrier code (default: DL)

        Returns:
            Availability details for the specified flight
        """
        try:
            flight_leg = FlightLeg(
                operating_carrier_code=operating_carrier,
                flight_num=flight_number,
                flight_departure_airport_code=departure_airport,
                departure_local_date=departure_date,
            )
            availability_response = await self.client.check_menu_availability(flight_legs=[flight_leg])
            return availability_response.model_dump(exclude_none=True)
        except Exception as e:
            return {
                "success": False,
                "error_message": str(e)
            }

    # @function_tool
    # async def get_cabin_menu(
    #     self,
    #     departure_date: str,
    #     flight_number: int,
    #     cabin_code: str,
    #     departure_airport: str = "ATL",
    #     operating_carrier: str = "DL",
    #     lang_cd: str = "en-US",
    #     check_availability: bool = False
    # ) -> Dict[str, Any]:
    #     """
    #     Get menu for a specific cabin class on a flight.
    #
    #     Args:
    #         departure_date: Flight departure date in YYYY-MM-DD format
    #         flight_number: Flight number
    #         cabin_code: Cabin class code (F=First, C=Business, Y=Economy)
    #         departure_airport: Departure airport code (default: ATL)
    #         operating_carrier: Airline carrier code (default: DL)
    #         lang_cd: Language code (default: en-US)
    #         check_availability: Whether to check menu availability first (default: False)
    #
    #     Returns:
    #         Menu details for the specified cabin class
    #     """
    #     try:
    #         # Optional: Check availability first
    #         if check_availability:
    #             flight_leg = FlightLeg(
    #                 operating_carrier_code=operating_carrier,
    #                 flight_num=flight_number,
    #                 flight_departure_airport_code=departure_airport,
    #                 departure_local_date=departure_date,
    #             )
    #             availability_response = await self.client.check_menu_availability(flight_legs=[flight_leg])
    #             availability = {
    #                 "success": availability_response.success,
    #                 "error_message": availability_response.error_message,
    #                 "availability": {}
    #             }
    #             if availability_response.success and availability_response.flight_legs:
    #                 flight_leg_availability = availability_response.flight_legs[0]
    #                 availability["availability"] = {
    #                     cabin.cabin_type_code: cabin.model_dump()
    #                     for cabin in flight_leg_availability.cabins
    #                 }
    #
    #             if not availability["success"]:
    #                 return CabinMenuResponse(
    #                     query_type="cabin_menu",
    #                     success=False,
    #                     error_message=f"Availability check failed: {availability['error_message']}",
    #                     availability_check=availability
    #                 ).model_dump(exclude_none=True)
    #
    #             # Check if this specific cabin has digital menu available
    #             cabin_availability = availability["availability"].get(cabin_code.upper())
    #             if not cabin_availability or not cabin_availability.get("digital_menu_available"):
    #                 return CabinMenuResponse(
    #                     query_type="cabin_menu",
    #                     success=False,
    #                     error_message=f"Digital menu not available for cabin {cabin_code}",
    #                     availability_check=availability
    #                 ).model_dump(exclude_none=True)
    #
    #         dep_date = date.fromisoformat(departure_date)
    #
    #         request = MenuQueryRequest(
    #             departure_date=dep_date,
    #             flight_number=flight_number,
    #             departure_airport=departure_airport,
    #             operating_carrier=operating_carrier,
    #             cabin_code=cabin_code,
    #             lang_cd=lang_cd
    #         )
    #
    #         response = await self.client.get_menu_by_flight(request)
    #
    #         # Filter for specific cabin if multiple returned
    #         target_cabin = None
    #         for cabin in response.menu_services:
    #             if cabin.cabin_code.upper() == cabin_code.upper():
    #                 target_cabin = cabin
    #                 break
    #
    #         if not target_cabin and response.menu_services:
    #             # If only one cabin returned, use it
    #             target_cabin = response.menu_services[0]
    #         elif not target_cabin:
    #             return CabinMenuResponse(
    #                 query_type="cabin_menu",
    #                 success=False,
    #                 error_message=f"No menu found for cabin {cabin_code}"
    #             ).model_dump(exclude_none=True)
    #
    #         flight_info = FlightInfo(
    #             carrier=response.carrier_code,
    #             flight_number=response.flight_number,
    #             date=response.departure_date,
    #             departure_airport=response.departure_airport
    #         )
    #
    #         cabin_detail = CabinDetail(
    #             code=target_cabin.cabin_code,
    #             name=target_cabin.cabin_name,
    #             service_time=target_cabin.service_time,
    #             special_notes=target_cabin.special_notes
    #         )
    #
    #         # Flatten all menu items from all menus for categorization
    #         all_menu_items = []
    #         for menu in target_cabin.menus:
    #             all_menu_items.extend(menu.menu_items)
    #
    #         categorized_menu = CategorizedMenu(
    #             appetizers=[
    #                 SimpleMenuItem(name=item.name, description=item.description, dietary_info=item.dietary_info)
    #                 for item in all_menu_items
    #                 if item.category.lower() in ['appetizer', 'starter', 'starters']
    #             ],
    #             entrees=[
    #                 SimpleMenuItem(name=item.name, description=item.description, dietary_info=item.dietary_info)
    #                 for item in all_menu_items
    #                 if item.category.lower() in ['entree', 'main', 'main course', 'main course']
    #             ],
    #             desserts=[
    #                 SimpleMenuItem(name=item.name, description=item.description, dietary_info=item.dietary_info)
    #                 for item in all_menu_items
    #                 if item.category.lower() in ['dessert', 'sweet', 'desserts']
    #             ],
    #             beverages=[
    #                 SimpleMenuItem(name=item.name, description=item.description, dietary_info=item.dietary_info)
    #                 for item in all_menu_items
    #                 if item.category.lower() in ['beverage', 'drink', 'beverages']
    #             ]
    #         )
    #
    #         return CabinMenuResponse(
    #             query_type="cabin_menu",
    #             flight_info=flight_info,
    #             cabin=cabin_detail,
    #             menu=categorized_menu,
    #             success=response.success,
    #             error_message=response.error_message,
    #             metadata={"api_response_time_ms": response.api_response_time_ms}
    #         ).model_dump(exclude_none=True)
    #
    #     except ValueError as e:
    #         return CabinMenuResponse(
    #             query_type="cabin_menu",
    #             success=False,
    #             error_message=f"Invalid date format: {e}. Use YYYY-MM-DD format."
    #         ).model_dump(exclude_none=True)
    #     except Exception as e:
    #         return CabinMenuResponse(
    #             query_type="cabin_menu",
    #             success=False,
    #             error_message=str(e)
    #         ).model_dump(exclude_none=True)

    # @function_tool
    # async def compare_cabins(
    #     self,
    #     departure_date: str,
    #     flight_number: int,
    #     cabin_codes: List[str],
    #     departure_airport: str = "ATL",
    #     operating_carrier: str = "DL"
    # ) -> Dict[str, Any]:
    #     """
    #     Compare menus across multiple cabin classes.
    #
    #     Args:
    #         departure_date: Flight departure date in YYYY-MM-DD format
    #         flight_number: Flight number
    #         cabin_codes: List of cabin codes to compare (e.g., ["F", "C", "Y"])
    #         departure_airport: Departure airport code (default: ATL)
    #         operating_carrier: Airline carrier code (default: DL)
    #
    #     Returns:
    #         Comparison of menus across specified cabin classes
    #     """
    #     try:
    #         dep_date = date.fromisoformat(departure_date)
    #
    #         request = MenuQueryRequest(
    #             departure_date=dep_date,
    #             flight_number=flight_number,
    #             departure_airport=departure_airport,
    #             operating_carrier=operating_carrier
    #         )
    #
    #         response = await self.client.get_menu_by_flight(request)
    #
    #         if not response.success:
    #             return CabinComparisonResponse(
    #                 query_type="cabin_comparison",
    #                 success=False,
    #                 error_message=response.error_message
    #             ).model_dump(exclude_none=True)
    #
    #         # Build comparison
    #         cabin_menus = {}
    #         for cabin_code in cabin_codes:
    #             cabin_menus[cabin_code] = None
    #             for cabin in response.menu_services:
    #                 if cabin.cabin_code.upper() == cabin_code.upper():
    #                     # Flatten all menu items for comparison
    #                     all_items = []
    #                     for menu in cabin.menus:
    #                         all_items.extend(menu.menu_items)
    #
    #                     cabin_menus[cabin_code] = CabinComparisonDetail(
    #                         name=cabin.cabin_name,
    #                         menu_summary={
    #                             "total_items": len(all_items),
    #                             "categories": list(set(item.category for item in all_items))
    #                         },
    #                         highlights=[
    #                             {"name": item.name, "category": item.category}
    #                             for item in all_items[:3]  # Top 3 items
    #                         ]
    #                     )
    #                     break
    #
    #         flight_info = FlightInfo(
    #             carrier=response.carrier_code,
    #             flight_number=response.flight_number,
    #             date=response.departure_date,
    #             departure_airport=response.departure_airport,
    #             arrival_airport=response.arrival_airport
    #         )
    #
    #         return CabinComparisonResponse(
    #             query_type="cabin_comparison",
    #             flight_info=flight_info,
    #             cabin_comparison=cabin_menus,
    #             success=True,
    #             metadata={"api_response_time_ms": response.api_response_time_ms}
    #         ).model_dump(exclude_none=True)
    #
    #     except ValueError as e:
    #         return CabinComparisonResponse(
    #             query_type="cabin_comparison",
    #             success=False,
    #             error_message=f"Invalid date format: {e}. Use YYYY-MM-DD format."
    #         ).model_dump(exclude_none=True)
    #     except Exception as e:
    #         return CabinComparisonResponse(
    #             query_type="cabin_comparison",
    #             success=False,
    #             error_message=str(e)
    #         ).model_dump(exclude_none=True)