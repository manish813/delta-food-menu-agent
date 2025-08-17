#!/usr/bin/env python3
"""
Usage example for the new menu availability integration
"""
import asyncio
import sys
import os

from src.client.delta_client import DeltaMenuClient
from src.tools.menu_tools import MenuTools

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def demonstrate_usage():
    """Demonstrate the new availability-first workflow"""
    print("🎯 Delta Menu Availability Integration - Usage Example")
    print("=" * 55)
    
    client = DeltaMenuClient()
    tools = MenuTools(client)
    
    try:
        # Example: Smart menu fetching workflow
        flight_details = {
            "departure_date": "2025-08-16",
            "flight_number": 30,
            "departure_airport": "ATL",
            "operating_carrier": "DL"
        }
        
        print(f"\n🔍 Checking availability for {flight_details['operating_carrier']}{flight_details['flight_number']} on {flight_details['departure_date']}")
        
        # Step 1: Check availability first
        availability = await tools.check_flight_menu_availability(**flight_details)
        
        if not availability["success"]:
            print(f"❌ Availability check failed: {availability['error_message']}")
            return
            
        print("\n📋 Availability Results:")
        available_cabins = []
        
        for cabin_code, info in availability["availability"].items():
            status = "✅ Available" if info["digital_menu_available"] else "❌ Not Available"
            print(f"  {cabin_code} ({info['cabin_name']}): {status}")
            
            if info["digital_menu_available"]:
                available_cabins.append(cabin_code)
        
        print(f"\n📊 Summary: {len(available_cabins)} cabins have digital menus available")
        
        # Step 2: Fetch menus only for available menu_services
        if available_cabins:
            print(f"\n🍽️ Fetching menus for available cabins: {', '.join(available_cabins)}")
            
            for cabin_code in available_cabins:
                print(f"\n--- {cabin_code} Class Menu ---")
                
                menu = await tools.get_cabin_menu(
                    departure_date=flight_details["departure_date"],
                    flight_number=flight_details["flight_number"],
                    cabin_code=cabin_code,
                    departure_airport=flight_details["departure_airport"],
                    operating_carrier=flight_details["operating_carrier"]
                )
                
                if menu["success"]:
                    print(f"Cabin: {menu['cabin']['name']}")
                    print(f"Service: {menu['cabin'].get('service_time', 'N/A')}")
                    
                    # Show menu highlights
                    all_items = []
                    for category, items in menu["menu"].items():
                        if items:
                            all_items.extend(items)
                    
                    if all_items:
                        print("Menu Highlights:")
                        for item in all_items[:3]:  # Top 3 items
                            print(f"  • {item['name']}")
                        print(f"  ... and {len(all_items) - 3} more items")
                    else:
                        print("No menu items available")
                else:
                    print(f"Failed to fetch menu: {menu['error_message']}")
        else:
            print("\n⚠️ No digital menus available for this flight")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client.close()


async def batch_availability_check():
    """Demonstrate checking multiple flights"""
    print("\n" + "=" * 55)
    print("📊 Batch Availability Check Example")
    print("=" * 55)
    
    client = DeltaMenuClient()
    tools = MenuTools(client)
    
    try:
        # Multiple flights to check
        flights_to_check = [
            {"date": "2025-08-16", "number": 30},
            {"date": "2025-08-16", "number": 996},
            {"date": "2025-08-16", "number": 444},
        ]
        
        print("\nChecking availability for multiple flights...")
        
        for flight in flights_to_check:
            availability = await tools.check_flight_menu_availability(
                departure_date=flight["date"],
                flight_number=flight["number"],
                departure_airport="ATL",
                operating_carrier="DL"
            )
            
            if availability["success"]:
                available_count = availability["summary"]["available_cabins"]
                total_count = availability["summary"]["total_cabins"]
                print(f"  DL{flight['number']}: {available_count}/{total_count} cabins available")
            else:
                print(f"  DL{flight['number']}: Error - {availability['error_message']}")
                
    except Exception as e:
        print(f"❌ Batch check failed: {e}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(demonstrate_usage())
    asyncio.run(batch_availability_check())