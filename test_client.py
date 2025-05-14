import requests
import json

def test_daily_limit_calculator():
    """Test program for Daily Spending Limit Calculator microservice"""
    
    # Set the URL of the microservice
    url = "http://localhost:5000/daily-limit"
    
    # Create sample budget data (using Garrett's example)
    budget_data = {
        "totalBudget": 2000.00,
        "reserve": 300.00,
        "expenses": [
            {"date": "2025-05-01", "amount": 500.00},
            {"date": "2025-05-05", "amount": 120.50}
        ],
        "endDate": "2025-05-31",
        "currentDate": "2025-05-07"
    }
    
    # Set headers
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": "test-123"
    }
    
    print("\n===== DAILY SPENDING LIMIT CALCULATOR DEMO =====\n")
    print("Sending request to:", url)
    print("\nRequest data:")
    print(json.dumps(budget_data, indent=2))
    
    try:
        # Send POST request to the microservice
        print("\nSending request...")
        response = requests.post(url, json=budget_data, headers=headers)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            
            print("\nResponse received successfully!")
            print("\nResponse data:")
            print(json.dumps(result, indent=2))
            
            # Display the important results
            print("\n===== RESULTS =====")
            print(f"Daily Spending Limit: ${result['dailyLimit']:.2f}")
            print(f"Remaining Budget: ${result['remainingBudget']:.2f}")
            print(f"Remaining Days: {result['remainingDays']}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            
            # Show error handling example
            print("\n===== ERROR HANDLING DEMO =====")
            print("Sending request with missing totalBudget field...")
            
            # Create invalid data (missing totalBudget)
            invalid_data = budget_data.copy()
            del invalid_data["totalBudget"]
            
            # Send invalid request
            error_response = requests.post(url, json=invalid_data, headers=headers)
            
            print(f"Response Status Code: {error_response.status_code}")
            print(f"Error Message: {error_response.json()['error']}")
            
            return True
        else:
            print(f"Error: HTTP Status {response.status_code}")
            print(response.text)
            return False
    
    except requests.exceptions.ConnectionError:
        print("Connection Error: Could not connect to the microservice.")
        print("Make sure the microservice server is running.")
        return False
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    test_daily_limit_calculator()