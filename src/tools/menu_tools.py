from typing import List, Dict, Any
from datetime import date

from agents import function_tool
from ..client.delta_client import DeltaMenuClient
from ..models.requests import MenuQueryRequest, FlightRequestValidation
from ..models.menu import FlightMenuResponse,  FlightLeg
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
        async def get_menu_by_flight(
                departure_date: str,
                flight_number: int,
                departure_airport: str,
                operating_carrier: str = "DL",
                cabin_codes: str = None
        ) -> Dict[str, Any]:
            """
           Get complete flight menu information for all cabin classes (First, Business, Economy)
           on a specific Delta flight. Returns detailed menu items, meal options, and service details
           for the requested flight date and route. Use this when customers ask about 'what food is served'
           or 'menu options' for a specific flight.

            Args:
                departure_date: Flight departure date in YYYY-MM-DD format
                flight_number: Flight number without carrier prefix (e.g., 30 for DL30)
                departure_airport: Departure airport code. 3 letter IATA airport code (e.g., ATL, LAX, JFK)
                operating_carrier: Airline carrier code (default: DL)
                cabin_codes: Optional comma-separated cabin codes to filter results (e.g., "F,C" for Delta Premium Select/First and Delta One/Business only. C=Delta One/Business, F=Delta Premium Select/First, W=IMC/Comfort, Y=IMC/Coach)

            Returns:
                Structured response with flight info and filtered cabin menus
            """
            logger.info(f"TOOL: get_menu_by_flight called - {operating_carrier}{flight_number} on {departure_date} from {departure_airport}")
            
            try:
                # Create MenuQueryRequest from individual parameters
                dep_date = date.fromisoformat(departure_date)
                logger.debug(f"Parsed departure date: {dep_date}")
                
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
        
        return get_menu_by_flight

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