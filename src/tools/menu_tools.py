from typing import List, Dict, Any
from datetime import date

from agents import function_tool
from ..client.delta_client import DeltaMenuClient
from ..models.requests import MenuQueryRequest
from ..models.menu import FlightMenuResponse, CabinMenu


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
                availability = await self.check_flight_menu_availability(
                    departure_date=departure_date,
                    flight_number=flight_number,
                    departure_airport=departure_airport,
                    operating_carrier=operating_carrier
                )
                
                if not availability["success"]:
                    return {
                        "query_type": "complete_menu",
                        "success": False,
                        "error_message": f"Availability check failed: {availability['error_message']}",
                        "availability_check": availability
                    }
                
                # Check if any cabin has digital menu available
                available_cabins = [
                    code for code, info in availability["availability"].items()
                    if info["digital_menu_available"]
                ]
                
                if not available_cabins:
                    return {
                        "query_type": "complete_menu",
                        "success": False,
                        "error_message": "No digital menus available for this flight",
                        "availability_check": availability
                    }
            
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
            return {
                "query_type": "complete_menu",
                "flight_info": {
                    "carrier": response.carrier_code,
                    "flight_number": response.flight_number,
                    "date": response.departure_date.isoformat(),
                    "departure_airport": response.departure_airport,
                    "arrival_airport": response.arrival_airport
                },
                "success": response.success,
                "error_message": response.error_message,
                "cabins": [
                    {
                        "cabin_code": cabin.cabin_code,
                        "cabin_name": cabin.cabin_name,
                        "service_time": cabin.service_time,
                        "special_notes": cabin.special_notes,
                        "menu_items": [
                            {
                                "name": item.name,
                                "description": item.description,
                                "category": item.category,
                                "dietary_info": item.dietary_info,
                                "allergens": item.allergens
                            }
                            for item in cabin.menu_items
                        ]
                    }
                    for cabin in response.cabins
                ],
                "metadata": {
                    "api_response_time_ms": response.api_response_time_ms
                }
            }
            
        except ValueError as e:
            return {
                "query_type": "complete_menu",
                "success": False,
                "error_message": f"Invalid date format: {e}. Use YYYY-MM-DD format."
            }
        except Exception as e:
            return {
                "query_type": "complete_menu",
                "success": False,
                "error_message": str(e)
            }
    
    @function_tool
    async def get_cabin_menu(
        self,
        departure_date: str,
        flight_number: int,
        cabin_code: str,
        departure_airport: str = "ATL",
        operating_carrier: str = "DL",
        lang_cd: str = "en-US",
        check_availability: bool = False
    ) -> Dict[str, Any]:
        """
        Get menu for a specific cabin class on a flight.
        
        Args:
            departure_date: Flight departure date in YYYY-MM-DD format
            flight_number: Flight number
            cabin_code: Cabin class code (F=First, C=Business, Y=Economy)
            departure_airport: Departure airport code (default: ATL)
            operating_carrier: Airline carrier code (default: DL)
            lang_cd: Language code (default: en-US)
            check_availability: Whether to check menu availability first (default: False)
            
        Returns:
            Menu details for the specified cabin class
        """
        try:
            # Optional: Check availability first
            if check_availability:
                availability = await self.check_flight_menu_availability(
                    departure_date=departure_date,
                    flight_number=flight_number,
                    departure_airport=departure_airport,
                    operating_carrier=operating_carrier
                )
                
                if not availability["success"]:
                    return {
                        "query_type": "cabin_menu",
                        "success": False,
                        "error_message": f"Availability check failed: {availability['error_message']}",
                        "availability_check": availability
                    }
                
                # Check if this specific cabin has digital menu available
                cabin_availability = availability["availability"].get(cabin_code.upper())
                if not cabin_availability or not cabin_availability.get("digital_menu_available"):
                    return {
                        "query_type": "cabin_menu",
                        "success": False,
                        "error_message": f"Digital menu not available for cabin {cabin_code}",
                        "availability_check": availability
                    }
            
            dep_date = date.fromisoformat(departure_date)
            
            request = MenuQueryRequest(
                departure_date=dep_date,
                flight_number=flight_number,
                departure_airport=departure_airport,
                operating_carrier=operating_carrier,
                cabin_code=cabin_code,
                lang_cd=lang_cd
            )
            
            response = await self.client.get_menu_by_flight(request)
            
            # Filter for specific cabin if multiple returned
            target_cabin = None
            for cabin in response.cabins:
                if cabin.cabin_code.upper() == cabin_code.upper():
                    target_cabin = cabin
                    break
            
            if not target_cabin and response.cabins:
                # If only one cabin returned, use it
                target_cabin = response.cabins[0]
            elif not target_cabin:
                return {
                    "query_type": "cabin_menu",
                    "success": False,
                    "error_message": f"No menu found for cabin {cabin_code}"
                }
            
            return {
                "query_type": "cabin_menu",
                "flight_info": {
                    "carrier": response.carrier_code,
                    "flight_number": response.flight_number,
                    "date": response.departure_date.isoformat(),
                    "departure_airport": response.departure_airport
                },
                "cabin": {
                    "code": target_cabin.cabin_code,
                    "name": target_cabin.cabin_name,
                    "service_time": target_cabin.service_time,
                    "special_notes": target_cabin.special_notes
                },
                "menu": {
                    "appetizers": [
                        {"name": item.name, "description": item.description}
                        for item in target_cabin.menu_items
                        if item.category.lower() in ['appetizer', 'starter']
                    ],
                    "entrees": [
                        {"name": item.name, "description": item.description}
                        for item in target_cabin.menu_items
                        if item.category.lower() in ['entree', 'main', 'main course']
                    ],
                    "desserts": [
                        {"name": item.name, "description": item.description}
                        for item in target_cabin.menu_items
                        if item.category.lower() in ['dessert', 'sweet']
                    ],
                    "beverages": [
                        {"name": item.name, "description": item.description}
                        for item in target_cabin.menu_items
                        if item.category.lower() in ['beverage', 'drink']
                    ]
                },
                "success": response.success,
                "error_message": response.error_message,
                "metadata": {
                    "api_response_time_ms": response.api_response_time_ms
                }
            }
            
        except ValueError as e:
            return {
                "query_type": "cabin_menu",
                "success": False,
                "error_message": f"Invalid date format: {e}. Use YYYY-MM-DD format."
            }
        except Exception as e:
            return {
                "query_type": "cabin_menu",
                "success": False,
                "error_message": str(e)
            }
    
    @function_tool
    async def compare_cabins(
        self,
        departure_date: str,
        flight_number: int,
        cabin_codes: List[str],
        departure_airport: str = "ATL",
        operating_carrier: str = "DL"
    ) -> Dict[str, Any]:
        """
        Compare menus across multiple cabin classes.
        
        Args:
            departure_date: Flight departure date in YYYY-MM-DD format
            flight_number: Flight number
            cabin_codes: List of cabin codes to compare (e.g., ["F", "C", "Y"])
            departure_airport: Departure airport code (default: ATL)
            operating_carrier: Airline carrier code (default: DL)
            
        Returns:
            Comparison of menus across specified cabin classes
        """
        try:
            dep_date = date.fromisoformat(departure_date)
            
            request = MenuQueryRequest(
                departure_date=dep_date,
                flight_number=flight_number,
                departure_airport=departure_airport,
                operating_carrier=operating_carrier
            )
            
            response = await self.client.get_menu_by_flight(request)
            
            if not response.success:
                return {
                    "query_type": "cabin_comparison",
                    "success": False,
                    "error_message": response.error_message
                }
            
            # Build comparison
            cabin_menus = {}
            for cabin_code in cabin_codes:
                cabin_menus[cabin_code] = None
                for cabin in response.cabins:
                    if cabin.cabin_code.upper() == cabin_code.upper():
                        cabin_menus[cabin_code] = {
                            "name": cabin.cabin_name,
                            "menu_summary": {
                                "total_items": len(cabin.menu_items),
                                "categories": list(set(item.category for item in cabin.menu_items))
                            },
                            "highlights": [
                                {"name": item.name, "category": item.category}
                                for item in cabin.menu_items[:3]  # Top 3 items
                            ]
                        }
                        break
            
            return {
                "query_type": "cabin_comparison",
                "flight_info": {
                    "carrier": response.carrier_code,
                    "flight_number": response.flight_number,
                    "date": response.departure_date.isoformat()
                },
                "cabin_comparison": cabin_menus,
                "success": True,
                "metadata": {
                    "api_response_time_ms": response.api_response_time_ms
                }
            }
            
        except ValueError as e:
            return {
                "query_type": "cabin_comparison",
                "success": False,
                "error_message": f"Invalid date format: {e}. Use YYYY-MM-DD format."
            }
        except Exception as e:
            return {
                "query_type": "cabin_comparison",
                "success": False,
                "error_message": str(e)
            }