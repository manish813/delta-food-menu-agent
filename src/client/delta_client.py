import httpx
from typing import Dict, Any, Optional
import time

from ..models.menu import FlightMenuResponse, CabinMenu, MenuItem, MenuAvailabilityResponse, FlightMenuAvailability, CabinAvailability
from ..models.requests import MenuQueryRequest
from .oauth_manager import DeltaOAuthManager


class DeltaMenuClient:
    """Client for interacting with Delta's flight menu API"""
    
    BASE_URL = "https://ifsobs-api.delta.com/CatFltMenuSvcRst/v1"
    
    DEFAULT_HEADERS = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.8',
        'channelid': 'DGMNPT',
        'origin': 'https://menu.delta.com',
        'priority': 'u=1, i',
        'referer': 'https://menu.delta.com/',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, oauth_manager: Optional[DeltaOAuthManager] = None):
        self.client = httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=30.0
        )
        self.oauth_manager = oauth_manager or DeltaOAuthManager()
    
    async def get_menu_by_flight(self, request: MenuQueryRequest) -> FlightMenuResponse:
        """Get menu for specific flight"""
        try:
            start_time = time.time()
            
            params = {
                'departureLocalDate': request.departure_date.isoformat(),
                'flightDepartureAirportCode': request.departure_airport,
                'flightNum': request.flight_number,
                'operatingCarrierCode': request.operating_carrier
            }
            
            if request.cabin_code:
                params['cabinCode'] = request.cabin_code
                
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
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_api_response(data, request, response_time_ms)
            else:
                return FlightMenuResponse(
                    carrier_code=request.operating_carrier,
                    flight_number=request.flight_number,
                    departure_date=request.departure_date,
                    departure_airport=request.departure_airport,
                    success=False,
                    error_message=f"API returned status code {response.status_code}",
                    api_response_time_ms=response_time_ms
                )
                
        except httpx.TimeoutException:
            return FlightMenuResponse(
                carrier_code=request.operating_carrier,
                flight_number=request.flight_number,
                departure_date=request.departure_date,
                departure_airport=request.departure_airport,
                success=False,
                error_message="Request timed out",
                api_response_time_ms=30000
            )
        except Exception as e:
            return FlightMenuResponse(
                carrier_code=request.operating_carrier,
                flight_number=request.flight_number,
                departure_date=request.departure_date,
                departure_airport=request.departure_airport,
                success=False,
                error_message=str(e)
            )
    
    def _parse_api_response(self, data: Dict[str, Any], request: MenuQueryRequest, response_time_ms: int) -> FlightMenuResponse:
        """Parse the Delta API response into our Pydantic models"""
        try:
            if not data or not data.get('flightMenus'):
                error_message = "Empty or invalid response from API"
                if isinstance(data, dict) and 'error' in data:
                    error_message = data['error']
                return FlightMenuResponse(
                    carrier_code=request.operating_carrier,
                    flight_number=request.flight_number,
                    departure_date=request.departure_date,
                    departure_airport=request.departure_airport,
                    success=False,
                    error_message=error_message,
                    api_response_time_ms=response_time_ms
                )

            flight_menu_data = data['flightMenus'][0]
            arrival_airport = flight_menu_data.get('flightArrivalAirportCode')
            cabins = []

            for menu_service_data in flight_menu_data.get('menuServices', []):
                cabin = self._parse_cabin_menu(menu_service_data)
                if cabin:
                    cabins.append(cabin)

            return FlightMenuResponse(
                carrier_code=request.operating_carrier,
                flight_number=request.flight_number,
                departure_date=request.departure_date,
                departure_airport=request.departure_airport,
                arrival_airport=arrival_airport,
                cabins=cabins,
                success=True,
                api_response_time_ms=response_time_ms
            )

        except (KeyError, IndexError) as e:
            return FlightMenuResponse(
                carrier_code=request.operating_carrier,
                flight_number=request.flight_number,
                departure_date=request.departure_date,
                departure_airport=request.departure_airport,
                success=False,
                error_message=f"Failed to parse response due to missing key: {str(e)}",
                api_response_time_ms=response_time_ms
            )
        except Exception as e:
            return FlightMenuResponse(
                carrier_code=request.operating_carrier,
                flight_number=request.flight_number,
                departure_date=request.departure_date,
                departure_airport=request.departure_airport,
                success=False,
                error_message=f"An unexpected error occurred during parsing: {str(e)}",
                api_response_time_ms=response_time_ms
            )

    def _parse_cabin_menu(self, menu_service_data: Dict[str, Any]) -> Optional[CabinMenu]:
        """Parse individual cabin menu data from a menuService object"""
        try:
            cabin_code = menu_service_data.get('cabinTypeCode', 'Unknown')
            cabin_name = menu_service_data.get('cabinTypeDesc', cabin_code)
            
            menu_items = []
            for menu_data in menu_service_data.get('menus', []):
                for item_data in menu_data.get('menuItems', []):
                    menu_item = self._parse_menu_item(item_data)
                    if menu_item:
                        menu_items.append(menu_item)
            
            if not menu_items:
                return None

            return CabinMenu(
                cabin_code=cabin_code,
                cabin_name=cabin_name,
                menu_items=menu_items,
                service_time=menu_service_data.get('primaryMenuServiceTypeDesc'),
                special_notes=menu_service_data.get('cabinWelcomeMessage')
            )
            
        except Exception:
            return None

    def _parse_menu_item(self, item_data: Dict[str, Any]) -> Optional[MenuItem]:
        """Parse individual menu item data"""
        try:
            dietary_info = [
                d.get('menuItemDietaryDesc') 
                for d in item_data.get('menuItemDietaryAsgmts', []) 
                if d.get('menuItemDietaryDesc')
            ]
            
            return MenuItem(
                name=item_data.get('menuItemDesc', 'Unknown Item'),
                description=item_data.get('menuItemAdditionalDesc'),
                category=item_data.get('menuItemTypeName', 'General'),
                dietary_info=dietary_info,
                allergens=[],
                image_url=None
            )
        except Exception:
            return None
    
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
    
    async def check_menu_availability(self, flight_legs: list) -> MenuAvailabilityResponse:
        """Check menu availability for flights using OAuth authentication"""
        start_time = time.time()
        
        try:
            # Get OAuth token
            access_token = await self.oauth_manager.get_access_token()
            
            # Prepare request data
            request_data = {
                "flightLegs": flight_legs
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
            if not data or 'flightLegs' not in data:
                return MenuAvailabilityResponse(
                    flight_legs=[],
                    success=False,
                    error_message="Invalid availability response format",
                    api_response_time_ms=response_time_ms
                )

            flight_legs = []
            for flight_data in data['flightLegs']:
                cabins = []
                for cabin_data in flight_data.get('cabins', []):
                    cabin = CabinAvailability(
                        cabin_type_code=cabin_data.get('cabinTypeCode', ''),
                        cabin_type_desc=cabin_data.get('cabinTypeDesc', ''),
                        pre_select_menu_available=cabin_data.get('preSelectMenuAvailable', False),
                        digital_menu_available=cabin_data.get('digitalMenuAvailable', False),
                        cabin_preselect_window_start_utc_ts=cabin_data.get('cabinPreselectWindowStartUtcTs'),
                        cabin_preselect_window_end_utc_ts=cabin_data.get('cabinPreselectWindowEndUtcTs')
                    )
                    cabins.append(cabin)

                flight = FlightMenuAvailability(
                    operating_carrier_code=flight_data.get('operatingCarrierCode', ''),
                    flight_num=flight_data.get('flightNum', 0),
                    flight_departure_airport_code=flight_data.get('flightDepartureAirportCode', ''),
                    departure_local_date=flight_data.get('departureLocalDate', ''),
                    status=str(flight_data.get('status', '')),
                    cabins=cabins
                )
                flight_legs.append(flight)

            return MenuAvailabilityResponse(
                flight_legs=flight_legs,
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
        await self.client.aclose()
        if hasattr(self, 'oauth_manager'):
            await self.oauth_manager.close()