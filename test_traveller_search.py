import requests
import json

def test_traveller_count():
    """Test that traveller count is properly captured and displayed in search results"""

    # Test data
    test_data = {
        'from_city': 'New York',
        'to_city': 'London',
        'travellers': '3',  # Test with 3 travellers
        'depart_date': '2024-12-25',
        'return_date': '2024-12-30',
        'flight_class': 'economy'
    }

    # Make POST request to search endpoint
    try:
        response = requests.post('http://127.0.0.1:5000/search', data=test_data)
        response.raise_for_status()

        # Check if the response contains the traveller count
        html_content = response.text

        # Look for the traveller count in the HTML
        if 'Travellers: <strong>3</strong>' in html_content:
            print("✅ SUCCESS: Traveller count (3) is correctly displayed in search results")
            return True
        else:
            print("❌ FAILURE: Traveller count not found in search results")
            print("Looking for: 'Travellers: <strong>3</strong>'")
            # Print a snippet of the HTML around where it should be
            if 'Travellers:' in html_content:
                start = html_content.find('Travellers:')
                end = html_content.find('</p>', start)
                print(f"Found: {html_content[start:end+4]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not connect to server: {e}")
        return False

def test_default_traveller_count():
    """Test default traveller count when not specified"""

    test_data = {
        'from_city': 'Paris',
        'to_city': 'Tokyo',
        'depart_date': '2024-12-25'
        # No travellers specified - should default to 1
    }

    try:
        response = requests.post('http://127.0.0.1:5000/search', data=test_data)
        response.raise_for_status()

        html_content = response.text

        if 'Travellers: <strong>1</strong>' in html_content:
            print("✅ SUCCESS: Default traveller count (1) is correctly displayed")
            return True
        else:
            print("❌ FAILURE: Default traveller count not found")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not connect to server: {e}")
        return False

if __name__ == "__main__":
    print("Testing Traveller Count in Search Results")
    print("=" * 50)

    # Test with 3 travellers
    test1_passed = test_traveller_count()
    print()

    # Test default (1 traveller)
    test2_passed = test_default_traveller_count()
    print()

    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED: Traveller count functionality is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED: Please check the implementation")
