import requests
import json

def test_location_api():
    """Simple test client for the location assistant API."""
    base_url = "http://localhost:5000/api/process-query"
    
    # Test cases with embedded location information
    test_cases = [
        # Test 1: Query with embedded coordinates
        {
            "name": "Embedded Coordinates",
            "payload": {
                "query": "Are there any hospitals near 37.7749, -122.4194?"
            }
        },
        # Test 2: Query with Google Maps URL
        {
            "name": "Google Maps URL",
            "payload": {
                "query": "Can I start a coffee shop here? https://www.google.com/maps?q=40.7128,-74.0060"
            }
        },
        # Test 3: Query with address
        {
            "name": "Named Location",
            "payload": {
                "query": "Are there any parks near Times Square, New York?"
            }
        },
        # Test 4: Query with no location information
        {
            "name": "No Location",
            "payload": {
                "query": "What's the nearest park?"
            }
        },
        # Test 5: Land purchase query with location
        {
            "name": "Land Purchase",
            "payload": {
                "query": "Can I buy land near Central Park, New York?"
            }
        }
    ]
    
    # Run each test case
    for test in test_cases:
        print(f"\n=== Testing: {test['name']} ===")
        print(f"Request: {json.dumps(test['payload'], indent=2)}")
        
        try:
            # Make the API request
            response = requests.post(base_url, json=test['payload'])
            
            # Print the response
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_location_api()