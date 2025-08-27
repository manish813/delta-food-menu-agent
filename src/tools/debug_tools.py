from typing import Dict, Any
import time
from datetime import date

from agents import function_tool
from ..client.delta_client import DeltaMenuClient
from ..models.requests import MenuQueryRequest


class DebugTools:
    """Tools for debugging and troubleshooting Delta API issues"""
    
    def __init__(self, client: DeltaMenuClient):
        self.client = client
    
    @function_tool
    async def validate_api_health(self) -> Dict[str, Any]:
        """
        Check if the Delta menu API is accessible and healthy.
        
        Returns:
            API health status and response time
        """
        try:
            health_check = await self.client.check_api_health()
            
            return {
                "tool": "api_health_check",
                "status": health_check.get('status', 'unknown'),
                "details": {
                    "status_code": health_check.get('status_code'),
                    "response_time_ms": health_check.get('response_time_ms'),
                    "error": health_check.get('error'),
                    "timestamp": time.time()
                },
                "recommendations": {
                    "healthy": "API is responding normally",
                    "unhealthy": "API may be experiencing issues. Check network connectivity or try again later."
                }
            }
            
        except Exception as e:
            return {
                "tool": "api_health_check",
                "status": "error",
                "error": str(e),
                "recommendations": [
                    "Check internet connection",
                    "Verify API endpoint URL",
                    "Check if Delta API is temporarily down"
                ]
            }
    

    @function_tool
    async def trace_api_call(
        self,
        departure_date: str,
        flight_number: int,
        departure_airport: str,
        operating_carrier: str = "DL"
    ) -> Dict[str, Any]:
        """
        Trace and log full API request/response details for debugging.
        
        Args:
            departure_date: Flight departure date in YYYY-MM-DD format
            flight_number: Flight number
            departure_airport: Departure airport code
            operating_carrier: Airline carrier code
            
        Returns:
            Complete request/response trace including timing and headers
        """
        try:
            # Build request parameters
            params = {
                'departureLocalDate': departure_date,
                'flightDepartureAirportCode': departure_airport,
                'flightNum': flight_number,
                'operatingCarrierCode': operating_carrier
            }
            
            # Calculate expected URL
            base_url = "https://ifsobs-api.delta.com/CatFltMenuSvcRst/v1/menuByFlight"
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{base_url}?{query_string}"
            
            # Get actual response (without making the call)
            # For now, return the trace information
            return {
                "tool": "api_trace",
                "request_details": {
                    "method": "GET",
                    "url": full_url,
                    "base_url": base_url,
                    "parameters": params,
                    "headers": {
                        "accept": "application/json, text/plain, */*",
                        "accept-language": "en-US,en;q=0.8",
                        "channelid": "DGMNPT",
                        "origin": "https://menu.delta.com",
                        "priority": "u=1, i",
                        "referer": "https://menu.delta.com/",
                        "sec-gpc": "1",
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "transactionid": "auto-generated-uuid"
                    }
                },
                "debug_info": {
                    "expected_response_format": "JSON with flight and cabin menu data",
                    "common_issues": [
                        "Invalid date format - use YYYY-MM-DD",
                        "Flight not found - check flight number and carrier",
                        "Airport code invalid - use 3-letter codes",
                        "Date too far in the past or future"
                    ],
                    "troubleshooting_tips": [
                        "Verify all parameters are correct",
                        "Check if flight operates on the specified date",
                        "Try a different date if menu unavailable",
                        "Use validate_flight_request tool to check parameters"
                    ]
                },
                "manual_testing": {
                    "curl_command": f"""curl '{full_url}' \\
  -H 'accept: application/json, text/plain, */*' \\
  -H 'accept-language: en-US,en;q=0.8' \\
  -H 'channelid: DGMNPT' \\
  -H 'origin: https://menu.delta.com' \\
  -H 'priority: u=1, i' \\
  -H 'referer: https://menu.delta.com/' \\
  -H 'sec-gpc: 1' \\
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'""",
                    "browser_url": full_url
                }
            }
            
        except ValueError as e:
            return {
                "tool": "api_trace",
                "error": f"Invalid date format: {e}",
                "recommendation": "Use YYYY-MM-DD format"
            }
        except Exception as e:
            return {
                "tool": "api_trace",
                "error": str(e),
                "recommendation": "Check all parameters are valid"
            }
    
    @function_tool
    async def diagnose_error(self, error_message: str) -> Dict[str, Any]:
        """
        Diagnose common API error messages and provide solutions.
        
        Args:
            error_message: The error message received from API or system
            
        Returns:
            Diagnosis and recommended solutions
        """
        error_lower = error_message.lower()
        
        # Common error patterns and solutions
        error_patterns = {
            "timeout": {
                "diagnosis": "Request timed out",
                "solutions": [
                    "Check internet connection",
                    "Try again in a few minutes",
                    "API may be temporarily slow"
                ]
            },
            "404": {
                "diagnosis": "Flight or route not found",
                "solutions": [
                    "Verify flight number and carrier code",
                    "Check if flight operates on the specified date",
                    "Confirm departure airport code is correct",
                    "Try a different date if flight doesn't operate daily"
                ]
            },
            "400": {
                "diagnosis": "Invalid request parameters",
                "solutions": [
                    "Check date format (use YYYY-MM-DD)",
                    "Verify airport codes are 3 letters",
                    "Ensure carrier code is 2 letters",
                    "Use validate_flight_request tool to check parameters"
                ]
            },
            "invalid date": {
                "diagnosis": "Date format or value issue",
                "solutions": [
                    "Use YYYY-MM-DD format",
                    "Ensure date is not in the past",
                    "Check date is within reasonable range (not > 1 year ahead)"
                ]
            },
            "no menu": {
                "diagnosis": "Menu data unavailable",
                "solutions": [
                    "Menu may not be available yet for this flight",
                    "Try a different date",
                    "Some flights may not have detailed menu information",
                    "Check if it's a codeshare flight"
                ]
            }
        }
        
        # Find matching pattern
        diagnosis = {
            "diagnosis": "Unknown error",
            "solutions": [
                "Check all request parameters",
                "Verify internet connection",
                "Try again in a few minutes",
                "Contact support if issue persists"
            ]
        }
        
        for pattern, info in error_patterns.items():
            if pattern in error_lower:
                diagnosis = info
                break
        
        return {
            "tool": "error_diagnosis",
            "error_message": error_message,
            "diagnosis": diagnosis["diagnosis"],
            "solutions": diagnosis["solutions"],
            "next_steps": [
                "Use validate_flight_request to check parameters",
                "Use validate_api_health to check API status",
                "Use trace_api_call to verify request format",
                "Try the request with different parameters"
            ]
        }