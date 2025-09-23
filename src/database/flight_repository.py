from .connection_pool import get_db_connection
from ..models.requests import FlightLookupRequest
from ..models.responses import FlightOption, FlightLookupResponse
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class FlightRepository:
    """Repository for flight-related database operations"""
    
    async def lookup_flights(self, request: FlightLookupRequest) -> FlightLookupResponse:
        """Query database for flights matching the route and date"""
        logger.info(f"Querying flights: {request.departure_airport} to {request.arrival_airport} on {request.departure_date}")
        
        try:
            with (await get_db_connection()) as connection:
                cursor = connection.cursor()
                
                query = """
                SELECT MKD_FLT_NB AS flight_number, 
                       SCH_DPRT_GDTTM AS departure_time, 
                       SCH_ARR_GDTTM AS arrival_time  
                FROM cat.flt_leg 
                WHERE TRUNC(SCH_DPRT_LDTTM) = to_date(:departure_date, 'yyyy-mm-dd') 
                  AND OPRTD_CRR_CD = :operating_carrier 
                  AND SCH_DPRT_ARPT_CD = :departure_airport 
                  AND SCH_ARR_ARPT_CD = :arrival_airport 
                  AND DB_OP_STT_CD = 'ADD'
                ORDER BY SCH_DPRT_GDTTM
                """
                
                cursor.execute(query, {
                    'departure_date': request.departure_date.strftime('%Y-%m-%d'),
                    'operating_carrier': request.operating_carrier,
                    'departure_airport': request.departure_airport,
                    'arrival_airport': request.arrival_airport
                })
                
                rows = cursor.fetchall()
                logger.debug(f"Query returned {len(rows)} flights")
                
                flights = [
                    FlightOption(
                        flight_number=int(row[0]),
                        departure_time=row[1].strftime('%H:%M') if row[1] else None,
                        arrival_time=row[2].strftime('%H:%M') if row[2] else None
                    )
                    for row in rows
                ]
                
                cursor.close()
                
                return FlightLookupResponse(
                    departure_airport=request.departure_airport,
                    arrival_airport=request.arrival_airport,
                    departure_date=request.departure_date.isoformat(),
                    operating_carrier=request.operating_carrier,
                    flights=flights,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}", exc_info=True)
            return FlightLookupResponse(
                departure_airport=request.departure_airport,
                arrival_airport=request.arrival_airport,
                departure_date=request.departure_date.isoformat(),
                operating_carrier=request.operating_carrier,
                flights=[],
                success=False,
                error_message=f"Database query failed: {str(e)}"
            )