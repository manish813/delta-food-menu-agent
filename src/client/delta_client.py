import httpx
from typing import Dict, Any, Optional
import time
from datetime import date

from ..models.menu import FlightMenuResponse, MenuAvailabilityResponse, \
    FlightMenuAvailability, CabinAvailability, FlightLeg, FlightMenuError
from ..models.requests import MenuQueryRequest, FlightRequestValidation, ValidationParameters, ValidationNextSteps
from .oauth_manager import DeltaOAuthManager
from ..utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(log_file='gradio_app.log')
logger = get_logger(__name__)

class DeltaMenuClient:
    """Client for interacting with Delta's flight menu API"""
    
    BASE_URL = "https://ifsobs-api.delta.com/CatFltMenuSvcRst/v1"
    
    DEFAULT_HEADERS = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.8',
        'channelId': 'DGMNPT',
        'origin': 'https://menu.delta.com',
        'priority': 'u=1, i',
        'referer': 'https://menu.delta.com/',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, oauth_manager: Optional[DeltaOAuthManager] = None):
        logger.info("Initializing DeltaMenuClient")
        self.client = httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=30.0
        )
        self.oauth_manager = oauth_manager or DeltaOAuthManager()
    
    async def get_menu_by_flight(self, request: MenuQueryRequest) -> FlightMenuResponse | FlightMenuError:
        """Get menu for specific flight"""
        logger.info(f"Getting menu for flight {request.operating_carrier}{request.flight_number} on {request.departure_date} from {request.departure_airport}")
        
        try:
            start_time = time.time()
            
            params = {
                'departureLocalDate': request.departure_date.isoformat(),
                'flightDepartureAirportCode': request.departure_airport,
                'flightNum': request.flight_number,
                'operatingCarrierCode': request.operating_carrier
            }
            logger.debug(f"API request params: {params}")
            
            # Generate transaction ID
            import uuid
            transaction_id = str(uuid.uuid4()).upper()
            
            headers = self.DEFAULT_HEADERS.copy()
            headers['transactionid'] = transaction_id

            response = await self.client.get(
                f"{self.BASE_URL}/menuByFlight",
                params=params,
                headers=headers
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"API response received: {response.status_code} ({response_time_ms}ms)")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return self._parse_api_response(data, request, response_time_ms)
            else:
                data = response.json()
                logger.warning(f"API returned non-200 status: {response.status_code} - {data}")
                return FlightMenuError(
                    success=False,
                    error_message=f"API returned {data}",
                )
                
        except httpx.TimeoutException:
            logger.error(f"API request timed out for flight {request.operating_carrier}{request.flight_number}")
            return FlightMenuResponse(
                operating_carrier_code=request.operating_carrier,
                flight_num=request.flight_number,
                flight_departure_date=request.departure_date.isoformat(),
                flight_departure_airport_code=request.departure_airport,
                success=False,
                error_message="Request timed out",
                api_response_time_ms=30000
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_menu_by_flight: {str(e)}", exc_info=True)
            return FlightMenuError(
                success=False,
                error_message=str(e)
            )
    
    def _parse_api_response(self, data: Dict[str, Any], request: MenuQueryRequest, response_time_ms: int) -> FlightMenuResponse | FlightMenuError:
        """Parse the Delta API response into our Pydantic models"""
        logger.debug("Parsing API response")
        
        try:
            if not data or not data.get('flightMenus'):
                error_message = "Empty or invalid response from API"
                if isinstance(data, dict) and 'error' in data:
                    error_message = data['error']
                logger.warning(f"Invalid API response: {error_message}")
                return FlightMenuResponse(
                    operating_carrier_code=request.operating_carrier,
                    flight_num=request.flight_number,
                    flight_departure_date=request.departure_date.isoformat(),
                    flight_departure_airport_code=request.departure_airport,
                    success=False,
                    error_message=error_message,
                    api_response_time_ms=response_time_ms
                )

            flight_menu_data = data['flightMenus'][0]
            logger.debug(f"Found flight menu data with keys: {list(flight_menu_data.keys())}")

            flight_menu_response = FlightMenuResponse.model_validate({
                **flight_menu_data,
                'success': True,
                'error_message': None,
                'api_response_time_ms': response_time_ms
            })
            logger.info(f"Successfully parsed menu response for {request.operating_carrier}{request.flight_number}")
            return flight_menu_response

        except Exception as e:
            logger.error(f"Error parsing API response: {str(e)}", exc_info=True)
            return FlightMenuError(
                success=False,
                error_message=f"An unexpected error occurred during parsing: {str(e)}",
            )


    def validate_flight_request(self, request: MenuQueryRequest) -> FlightRequestValidation:
        """
        Validate flight request parameters before making API calls.

        Args:
            request: MenuQueryRequest model with flight parameters

        Returns:
            FlightRequestValidation model with validation results
        """
        issues = []
        recommendations = []

        # Check if date is in the past
        if request.departure_date < date.today():
            issues.append("Departure date is in the past")
            recommendations.append("Use a future date or today's date")

        # Check if date is too far in the future (more than 1 year)
        from datetime import timedelta
        if request.departure_date > date.today() + timedelta(days=365):
            issues.append("Departure date is more than 1 year in the future")
            recommendations.append("Menu data may not be available for flights more than 1 year ahead")

        # Validate flight number (already validated by Pydantic)
        if request.flight_number > 9999:
            issues.append("Invalid flight number")
            recommendations.append("Flight number should be between 1 and 9999")

        # Validate airport code
        if len(request.departure_airport) != 3 or not request.departure_airport.isalpha():
            issues.append("Invalid airport code format")
            recommendations.append("Airport code should be 3 letters (e.g., ATL, LAX, JFK)")

        # Validate carrier code
        if len(request.operating_carrier) != 2 or not request.operating_carrier.isalpha():
            issues.append("Invalid carrier code format")
            recommendations.append("Carrier code should be 2 letters (e.g., DL, AA, UA)")

        return FlightRequestValidation(
            is_valid=len(issues) == 0,
            issues=issues,
            recommendations=recommendations,
            parameters=ValidationParameters(
                flight_departure_date=request.departure_date.isoformat(),
                flight_number=request.flight_number,
                flight_departure_airport=request.departure_airport,
                operating_carrier=request.operating_carrier
            ),
            next_steps=ValidationNextSteps()
        )

    async def check_api_health(self) -> Dict[str, Any]:
        """Check if the Delta API is accessible"""
        try:
            # Try a simple request to check if API is up
            response = await self.client.get(
                f"{self.BASE_URL}/menuByFlight",
                params={
                    'departureLocalDate': '2025-08-13',
                    'flightDepartureAirportCode': 'ATL',
                    'flightNum': 30,
                    'operatingCarrierCode': 'DL'
                },
                timeout=10.0
            )
            
            return {
                'status': 'healthy' if response.status_code < 500 else 'unhealthy',
                'status_code': response.status_code,
                'response_time_ms': int(response.elapsed.total_seconds() * 1000)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def check_menu_availability(self, flight_legs: list[FlightLeg]) -> MenuAvailabilityResponse:
        """Check menu availability for flights using OAuth authentication"""
        start_time = time.time()
        
        try:
            # Get OAuth token
            access_token = await self.oauth_manager.get_access_token()
            
            # Prepare request data
            request_data = {
                "flightLegs": [leg.model_dump(by_alias=True) for leg in flight_legs]
            }
            
            # Generate transaction ID
            import uuid
            transaction_id = str(uuid.uuid4()).upper()
            
            # Headers for availability API
            headers = {
                'accept': 'application/json',
                'channelID': 'EM',
                'TransactionID': transaction_id,
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = await self.client.post(
                f"{self.BASE_URL}/digitalMenuAvailability",
                json=request_data,
                headers=headers
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_availability_response(data, response_time_ms)
            else:
                return MenuAvailabilityResponse(
                    flight_legs=[],
                    success=False,
                    error_message=f"Availability API returned status code {response.status_code}",
                    api_response_time_ms=response_time_ms
                )
                
        except httpx.TimeoutException:
            return MenuAvailabilityResponse(
                flight_legs=[],
                success=False,
                error_message="Availability request timed out",
                api_response_time_ms=30000
            )
        except Exception as e:
            return MenuAvailabilityResponse(
                flight_legs=[],
                success=False,
                error_message=str(e)
            )

    def _parse_availability_response(self, data: Dict[str, Any], response_time_ms: int) -> MenuAvailabilityResponse:
        """Parse the menu availability API response"""
        try:
            return MenuAvailabilityResponse(
                flight_legs=data.get('flightLegs', []),
                success=True,
                api_response_time_ms=response_time_ms
            )
        except Exception as e:
            return MenuAvailabilityResponse(
                flight_legs=[],
                success=False,
                error_message=f"Failed to parse availability response: {str(e)}",
                api_response_time_ms=response_time_ms
            )

    async def close(self):
        """Close the HTTP client"""
        logger.info("Closing DeltaMenuClient")
        await self.client.aclose()
        if hasattr(self, 'oauth_manager'):
            await self.oauth_manager.close()
        logger.debug("DeltaMenuClient closed")