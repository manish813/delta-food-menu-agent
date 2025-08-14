#!/usr/bin/env python3
"""
Test script to verify the new menu availability integration
"""
import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from client.delta_client import DeltaMenuClient
from tools.menu_tools import MenuTools


async def test_availability():
    """Test the new availability check functionality"""
    print("🧪 Testing Delta Menu Availability Integration")
    print("=" * 50)
    
    # Initialize client and tools
    client = DeltaMenuClient()
    tools = MenuTools(client)
    
    try:
        # Test availability check
        print("\n1. Testing menu availability check...")
        availability = await tools.check_flight_menu_availability(
            departure_date="2025-08-16",
            flight_number=30,
            departure_airport="ATL",
            operating_carrier="DL"
        )
        
        if availability["success"]:
            print("✅ Availability check successful!")
            print(f"Flight: {availability['flight_info']['carrier']}{availability['flight_info']['flight_number']}")
            print(f"Date: {availability['flight_info']['date']}")
            print(f"From: {availability['flight_info']['departure_airport']}")
            print()
            
            print("📊 Cabin Availability:")
            for cabin_code, info in availability["availability"].items():
                status = "✅ Available" if info["digital_menu_available"] else "❌ Not Available"
                print(f"  {cabin_code} ({info['cabin_name']}): {status}")
                
            print()
            print(f"📈 Summary: {availability['summary']['available_cabins']} of {availability['summary']['total_cabins']} cabins have digital menus")
            print(f"🎯 Action: {availability['summary']['recommended_action']}")
            
            # Test conditional menu fetching
            if availability["summary"]["recommended_action"] == "Fetch menu data":
                print("\n2. Testing conditional menu fetch...")
                available_cabins = [
                    code for code, info in availability["availability"].items() 
                    if info["digital_menu_available"]
                ]
                
                if available_cabins:
                    cabin_to_test = available_cabins[0]
                    print(f"Fetching menu for cabin {cabin_to_test}...")
                    
                    menu = await tools.get_cabin_menu(
                        departure_date="2025-08-16",
                        flight_number=30,
                        cabin_code=cabin_to_test,
                        departure_airport="ATL",
                        operating_carrier="DL"
                    )
                    
                    if menu["success"]:
                        print(f"✅ Menu fetched successfully for cabin {cabin_to_test}")
                        print(f"   Cabin: {menu['cabin']['name']}")
                        print(f"   Total items: {len(menu['menu']['appetizers']) + len(menu['menu']['entrees']) + len(menu['menu']['desserts']) + len(menu['menu']['beverages'])}")
                    else:
                        print(f"❌ Failed to fetch menu: {menu['error_message']}")
                        
        else:
            print(f"❌ Availability check failed: {availability['error_message']}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_availability())