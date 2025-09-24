from datetime import date
from typing import Dict, Any

from agents import function_tool

from ..client.delta_client import DeltaMenuClient
from ..models.menu import FlightLeg
from ..models.requests import MenuQueryRequest, FlightLookupRequest
from ..models.responses import (
    CompleteMenuResponse,
    FlightInfo,
)
from ..utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(log_file='gradio_app.log')
logger = get_logger(__name__)

class MenuTools:
    """Tools for querying Delta flight menus"""
    
    def __init__(self, client: DeltaMenuClient):
        self.client = client
    
    def get_menu_by_flight_tool(self):
        """Create the menu function tool"""

        @function_tool
        async def get_flight_menu(
                departure_date: str,
                departure_airport: str,
                flight_number: int = None,
                arrival_airport: str = None,
                operating_carrier: str = "DL",
                cabin_codes: str = None
        ) -> Dict[str, Any]:
            """
           Get complete flight menu information for Delta flights. If flight_number is not provided,
           will lookup available flights for the route and ask user to select. Returns detailed menu items,
           meal options, and service details. Use this when customers ask about 'what food is served'
           or 'menu options' for flights.

            Args:
                departure_date: Flight departure date in YYYY-MM-DD format
                departure_airport: Departure airport code (e.g., ATL, LAX, JFK)
                flight_number: Optional flight number without carrier prefix (e.g., 30 for DL30)
                arrival_airport: Optional arrival airport code (required if flight_number not provided)
                operating_carrier: Airline carrier code (default: DL)
                cabin_codes: Optional comma-separated cabin codes to filter results (C=Delta One/Business, F=Delta Premium Select/First, W=Comfort+, Y=Main Cabin/Economy)

            Returns:
                Flight menu information or flight options for selection
            """
            logger.info(f"TOOL: get_menu_by_flight called - {operating_carrier}{flight_number or 'TBD'} on {departure_date} from {departure_airport} to {arrival_airport or 'TBD'}")
            
            try:
                dep_date = date.fromisoformat(departure_date)
                logger.debug(f"Parsed departure date: {dep_date}")
                
                # If no flight number provided, lookup flights by route
                if flight_number is None:
                    if not arrival_airport:
                        return {
                            "query_type": "flight_lookup",
                            "success": False,
                            "error_message": "arrival_airport is required when flight_number is not provided"
                        }
                    
                    lookup_request = FlightLookupRequest(
                        departure_date=dep_date,
                        departure_airport=departure_airport,
                        arrival_airport=arrival_airport,
                        operating_carrier=operating_carrier
                    )
                    
                    lookup_response = await self.client.lookup_flights(lookup_request)
                    
                    if not lookup_response.success or not lookup_response.flights:
                        return {
                            "query_type": "flight_lookup",
                            "success": False,
                            "error_message": lookup_response.error_message or "No flights found for this route"
                        }
                    
                    # Return flight options for user selection
                    return {
                        "query_type": "flight_selection",
                        "success": True,
                        "message": f"Found {len(lookup_response.flights)} flights from {departure_airport} to {arrival_airport} on {departure_date}. Please select a flight:",
                        "flights": lookup_response.flights,
                        "route_info": {
                            "departure_airport": departure_airport,
                            "arrival_airport": arrival_airport,
                            "departure_date": departure_date,
                            "operating_carrier": operating_carrier
                        }
                    }
                
                # Proceed with menu query using provided flight number
                request = MenuQueryRequest(
                    departure_date=dep_date,
                    flight_number=flight_number,
                    departure_airport=departure_airport,
                    operating_carrier=operating_carrier
                )
                logger.debug("MenuQueryRequest created")

                flight_request_validation = self.client.validate_flight_request(request)
                logger.debug(f"Request validation result: {flight_request_validation.is_valid}")
                if not flight_request_validation.is_valid:
                    logger.warning(f"Request validation failed: {flight_request_validation.issues}")
                    return flight_request_validation.model_dump(exclude_none=True)

                # Get menu data
                logger.debug("Calling client.get_menu_by_flight")
                response = await self.client.get_menu_by_flight(request)
                logger.debug(f"Client response success: {response.success}")
                
                # Filter menu services by cabin codes if specified
                filtered_menu_services = response.menu_services
                if cabin_codes and response.menu_services:
                    requested_cabins = [code.strip().upper() for code in cabin_codes.split(',')]
                    filtered_menu_services = [
                        service for service in response.menu_services 
                        if service.cabin_type_code and service.cabin_type_code.upper() in requested_cabins
                    ]
                    logger.debug(f"Filtered menu services from {len(response.menu_services)} to {len(filtered_menu_services)} for cabins: {requested_cabins}")

                # Format response for readability
                flight_info = FlightInfo(
                    carrier=response.operating_carrier_code,
                    flight_number=response.flight_num,
                    date=dep_date,
                    departure_airport=response.flight_departure_airport_code,
                    arrival_airport=getattr(response, 'flight_arrival_airport_code', None)
                )
                logger.debug("Flight info formatted")

                result = CompleteMenuResponse(
                    query_type="complete_menu",
                    flight_info=flight_info,
                    success=response.success,
                    error_message=response.error_message,
                    menu_services=filtered_menu_services,
                    metadata={"api_response_time_ms": response.api_response_time_ms}
                ).model_dump(exclude_none=True)
                
                logger.info(f"TOOL: get_menu_by_flight completed successfully - {len(filtered_menu_services or [])} menu services returned")
                logger.info(f"Returning get menu by flight result: {result}")
                return result

            except Exception as e:
                logger.error(f"TOOL: get_menu_by_flight failed - {str(e)}", exc_info=True)
                return CompleteMenuResponse(
                    query_type="complete_menu",
                    success=False,
                    error_message=str(e)
                ).model_dump(exclude_none=True)
        
        return get_flight_menu

    def check_menu_availability_tool(self):
        """Create the menu availability function tool"""

        @function_tool
        async def check_menu_availability(
                departure_date: str,
                flight_number: int,
                departure_airport: str,
                operating_carrier: str = "DL",
        ) -> Dict[str, Any]:
            """
            Check menu availability for a specific flight. Also use to verify if menus exist.
            Can verify preselect eligibility and also time windows for preselect for cabins.

            Args:
                departure_date: Flight departure date in YYYY-MM-DD format
                flight_number: Flight number
                departure_airport: Departure airport code
                operating_carrier: Airline carrier code (default: DL)

            Returns:
                Availability details for the specified flight
            """
            logger.info(f"TOOL: check_menu_availability called - {operating_carrier}{flight_number} on {departure_date} from {departure_airport}")

            try:
                flight_leg = FlightLeg(
                    operating_carrier_code=operating_carrier,
                    flight_num=flight_number,
                    flight_departure_airport_code=departure_airport,
                    departure_local_date=departure_date,
                )
                logger.debug("FlightLeg created for availability check")
                
                availability_response = await self.client.check_menu_availability(flight_legs=[flight_leg])
                logger.info(f"TOOL: check_menu_availability completed - Success: {availability_response.success}")
                return availability_response.model_dump(exclude_none=True)

            except Exception as e:
                logger.error(f"TOOL: check_menu_availability failed - {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error_message": str(e)
                }
        return check_menu_availability
    
    def lookup_flights_tool(self):
        """Create the flight lookup function tool"""

        @function_tool
        async def lookup_flights(
                departure_date: str,
                departure_airport: str,
                arrival_airport: str,
                operating_carrier: str = "DL"
        ) -> Dict[str, Any]:
            """
            Find available flight numbers for a specific route and date. Use this when users
            provide departure/arrival airports and date but no flight number.

            Args:
                departure_date: Flight departure date in YYYY-MM-DD format
                departure_airport: Departure airport code (e.g., ATL, LAX, JFK)
                arrival_airport: Arrival airport code (e.g., LHR, CDG, NRT)
                operating_carrier: Airline carrier code (default: DL)

            Returns:
                List of available flights for the route and date
            """
            logger.info(f"TOOL: lookup_flights called - {departure_airport} to {arrival_airport} on {departure_date}")

            try:
                dep_date = date.fromisoformat(departure_date)
                
                lookup_request = FlightLookupRequest(
                    departure_date=dep_date,
                    departure_airport=departure_airport,
                    arrival_airport=arrival_airport,
                    operating_carrier=operating_carrier
                )
                
                response = await self.client.lookup_flights(lookup_request)
                logger.info(f"TOOL: lookup_flights completed - Found {len(response.flights)} flights")
                
                return {
                    "query_type": "flight_lookup",
                    "success": response.success,
                    "error_message": response.error_message,
                    "route_info": {
                        "departure_airport": departure_airport,
                        "arrival_airport": arrival_airport,
                        "departure_date": departure_date,
                        "operating_carrier": operating_carrier
                    },
                    "flights": response.flights
                }

            except Exception as e:
                logger.error(f"TOOL: lookup_flights failed - {str(e)}", exc_info=True)
                return {
                    "query_type": "flight_lookup",
                    "success": False,
                    "error_message": str(e)
                }
        
        return lookup_flights