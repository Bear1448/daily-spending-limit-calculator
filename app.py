from flask import Flask, request, jsonify
from datetime import datetime
import math
import uuid

app = Flask(__name__)

@app.route('/daily-limit', methods=['POST'])
def calculate():
    try:
        # Get correlation ID from header or generate a new one
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        
        # Get JSON data from request
        data = request.get_json()
        
        # Check if data exists
        if not data:
            return jsonify({"error": "Request body must be valid JSON"}), 400
        
        # Check for required fields
        required_fields = ['totalBudget', 'reserve', 'expenses', 'endDate', 'currentDate']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Calculate total expenses
        total_expenses = sum(expense['amount'] for expense in data['expenses'])
        
        # Calculate remaining budget
        remaining_budget = data['totalBudget'] - data['reserve'] - total_expenses
        
        # Calculate remaining days
        end_date = datetime.strptime(data['endDate'], '%Y-%m-%d')
        current_date = datetime.strptime(data['currentDate'], '%Y-%m-%d')
        remaining_days = (end_date - current_date).days + 1  # Include current day
        
        # Handle case where budget period has ended
        if remaining_days <= 0:
            return jsonify({
                "dailyLimit": 0.00,
                "remainingBudget": remaining_budget,
                "remainingDays": 0,
                "status": "warning",
                "message": "Budget period has ended.",
                "correlationId": correlation_id
            })
        
        # Calculate daily limit (rounded down to nearest cent)
        daily_limit = remaining_budget / remaining_days
        daily_limit = math.floor(daily_limit * 100) / 100
        
        # Determine status based on threshold (20% of total budget)
        threshold = 0.2 * data['totalBudget']
        
        if remaining_budget <= threshold:
            status = "warning"
            message = "You are within 20% of your monthly budget."
        else:
            status = "ok"
            message = "You are on track with your budget."
        
        # Return results
        return jsonify({
            "dailyLimit": daily_limit,
            "remainingBudget": remaining_budget,
            "remainingDays": remaining_days,
            "status": status,
            "message": message,
            "correlationId": correlation_id
        })
        
    except Exception as e:
        # Handle errors
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Daily Spending Limit Calculator microservice...")
    print("Server running at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)