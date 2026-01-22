import requests
import json

# Test the traveller to payment flow
def test_traveller_flow():
    # Simulate traveller form data
    traveller_data = {
        "travellers": json.dumps([{
            "full_name": "John Doe",
            "age": 30,
            "passport_number": "X1234567",
            "nationality": "Not Provided",
            "gender": "Not Specified",
            "email": "john@example.com",
            "phone_number": "Not Provided"
        }]),
        "flight_id": "1",
        "total_amount": "500"
    }

    # Test the traveller endpoint
    try:
        response = requests.post("http://127.0.0.1:5000/traveller", data=traveller_data)
        print(f"Traveller endpoint response: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 401:
            print("❌ Authentication required - need to login first")
        elif response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Traveller data saved successfully")
                print("✅ Should redirect to payment page")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"❌ Error testing traveller flow: {e}")

if __name__ == "__main__":
    test_traveller_flow()
