# Daily Spending Limit Calculator

A microservice that calculates how much money a user can spend each day while staying within their monthly budget.

## Communication Contract

### How to REQUEST data from the microservice:

To request data from this microservice, you need to send an HTTP POST request to the `/daily-limit` endpoint with your budget data in JSON format.

#### Required request parameters:
- `totalBudget`: The total monthly budget amount
- `reserve`: Amount set aside as emergency/reserve funds
- `expenses`: List of expenses, each with a date and amount
- `endDate`: Last day of the budget period (YYYY-MM-DD format)
- `currentDate`: Current date (YYYY-MM-DD format)

#### Example request code:

```python
import requests
import json

url = "http://localhost:5000/daily-limit"
headers = {
    "Content-Type": "application/json",
    "X-Correlation-ID": "your-request-id"  # optional
}
data = {
    "totalBudget": 2000.00,
    "reserve": 300.00,
    "expenses": [
        {"date": "2025-05-01", "amount": 500.00},
        {"date": "2025-05-05", "amount": 120.50}
    ],
    "endDate": "2025-05-31",
    "currentDate": "2025-05-07"
}

response = requests.post(url, headers=headers, json=data)
