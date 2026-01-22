import requests
import json
from bs4 import BeautifulSoup

def test_full_booking_flow():
    """Test the complete booking flow with traveller count"""

    session = requests.Session()

    print("🧪 Testing Complete Booking Flow with Traveller Count")
    print("=" * 60)

    # Step 1: Test search with 4 travellers
    print("1. Testing Search with 4 Travellers...")
    search_data = {
        'from_city': 'New York',
        'to_city': 'London',
        'travellers': '4',
        'depart_date': '2024-12-25',
        'return_date': '2024-12-30',
        'flight_class': 'business'
    }

    try:
        response = session.post('http://127.0.0.1:5000/search', data=search_data)
        response.raise_for_status()

        if 'Travellers: <strong>4</strong>' in response.text:
            print("✅ Search Results: Traveller count (4) displayed correctly")
        else:
            print("❌ Search Results: Traveller count not found")
            return False

        # Parse HTML to find flight links (both static and dynamic)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for static flight links first
        flight_links = soup.find_all('a', href=True, string='Select Flight')

        if not flight_links:
            # If no static links, look for dynamic flight containers
            flight_containers = soup.find_all('div', class_='flight-item')
            if not flight_containers:
                print("❌ No flight selection links or containers found")
                return False
            # For dynamic flights, we need to simulate the JavaScript behavior
            # Extract flight data from the first container
            first_container = flight_containers[0]
            flight_link = first_container.find('a', class_='btn-pay')
            if not flight_link:
                print("❌ No flight selection link found in container")
                return False
            first_flight_href = flight_link['href']
        else:
            # Use static flight link
            first_flight_href = flight_links[0]['href']

        print(f"✅ Found flight link: {first_flight_href}")

        # Step 2: Test traveller details page
        print("\n2. Testing Traveller Details Page...")
        traveller_url = f"http://127.0.0.1:5000{first_flight_href}"

        response = session.get(traveller_url)
        response.raise_for_status()

        if 'Please fill in the details for 4 traveller(s)' in response.text:
            print("✅ Traveller Page: Correct traveller count (4) displayed")
        else:
            print("❌ Traveller Page: Incorrect traveller count")
            return False

        # Count the number of traveller forms
        soup = BeautifulSoup(response.text, 'html.parser')
        traveller_sections = soup.find_all('h5', string=lambda text: text and 'Traveller' in text)
        if len(traveller_sections) == 4:
            print("✅ Traveller Page: Correct number of forms (4) rendered")
        else:
            print(f"❌ Traveller Page: Expected 4 forms, found {len(traveller_sections)}")
            return False

        print("\n🎉 FULL BOOKING FLOW TEST PASSED!")
        print("✅ Search → Traveller Details: Traveller count maintained correctly")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not complete booking flow test: {e}")
        return False

def test_edge_cases():
    """Test edge cases for traveller count"""

    print("\n🧪 Testing Edge Cases")
    print("=" * 30)

    # Test minimum travellers (1)
    print("Testing minimum travellers (1)...")
    search_data = {'from_city': 'Paris', 'to_city': 'Rome', 'travellers': '1'}
    response = requests.post('http://127.0.0.1:5000/search', data=search_data)
    if 'Travellers: <strong>1</strong>' in response.text:
        print("✅ Min travellers (1): OK")
    else:
        print("❌ Min travellers (1): FAILED")

    # Test maximum travellers (9)
    print("Testing maximum travellers (9)...")
    search_data = {'from_city': 'Tokyo', 'to_city': 'Sydney', 'travellers': '9'}
    response = requests.post('http://127.0.0.1:5000/search', data=search_data)
    if 'Travellers: <strong>9</strong>' in response.text:
        print("✅ Max travellers (9): OK")
    else:
        print("❌ Max travellers (9): FAILED")

    # Test invalid travellers (should default to 1)
    print("Testing invalid travellers (0)...")
    search_data = {'from_city': 'Berlin', 'to_city': 'Vienna', 'travellers': '0'}
    response = requests.post('http://127.0.0.1:5000/search', data=search_data)
    if 'Travellers: <strong>1</strong>' in response.text:
        print("✅ Invalid travellers (0): Defaults to 1 - OK")
    else:
        print("❌ Invalid travellers (0): FAILED")

if __name__ == "__main__":
    # Run full booking flow test
    flow_test_passed = test_full_booking_flow()

    # Run edge case tests
    test_edge_cases()

    print("\n" + "=" * 60)
    if flow_test_passed:
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅ Traveller count is properly maintained throughout the booking flow")
    else:
        print("⚠️  SOME TESTS FAILED - Please check the implementation")
