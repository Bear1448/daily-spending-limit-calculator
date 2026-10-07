"""Daily Spending Limit Calculator microservice.

POST /daily-limit with a monthly budget, a reserve, the expenses so far, and
the current/end dates. Returns how much can be spent per day for the rest of
the period without dipping into the reserve.
"""

import math
import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, request

app = Flask(__name__)

DATE_FORMAT = "%Y-%m-%d"
WARNING_THRESHOLD = 0.20  # warn when 20% or less of the total budget remains
REQUIRED_FIELDS = ("totalBudget", "reserve", "expenses", "endDate", "currentDate")


class ValidationError(ValueError):
    """Raised when the request body is missing data or has bad values."""


def _number(value, field):
    # bool is a subclass of int in Python, so reject it explicitly
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"'{field}' must be a number")
    if math.isnan(value) or math.isinf(value):
        raise ValidationError(f"'{field}' must be a finite number")
    if value < 0:
        raise ValidationError(f"'{field}' cannot be negative")
    return float(value)


def _date(value, field):
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string in YYYY-MM-DD format")
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise ValidationError(f"'{field}' must be in YYYY-MM-DD format") from None


def parse_request(data):
    """Validate the JSON body and return clean values, or raise ValidationError."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")

    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    total_budget = _number(data["totalBudget"], "totalBudget")
    reserve = _number(data["reserve"], "reserve")
    if reserve > total_budget:
        raise ValidationError("'reserve' cannot be larger than 'totalBudget'")

    expenses = data["expenses"]
    if not isinstance(expenses, list):
        raise ValidationError("'expenses' must be a list")
    total_expenses = 0.0
    for i, expense in enumerate(expenses):
        if not isinstance(expense, dict) or "amount" not in expense:
            raise ValidationError(f"expenses[{i}] must be an object with an 'amount'")
        total_expenses += _number(expense["amount"], f"expenses[{i}].amount")

    current_date = _date(data["currentDate"], "currentDate")
    end_date = _date(data["endDate"], "endDate")

    return total_budget, reserve, total_expenses, current_date, end_date


def calculate_daily_limit(total_budget, reserve, total_expenses, current_date, end_date):
    """Core math, kept separate from Flask so it can be unit tested directly."""
    remaining_budget = round(total_budget - reserve - total_expenses, 2)
    remaining_days = (end_date - current_date).days + 1  # include today

    if remaining_days <= 0:
        return {
            "dailyLimit": 0.00,
            "remainingBudget": remaining_budget,
            "remainingDays": 0,
            "status": "ended",
            "message": "Budget period has ended.",
        }

    if remaining_budget <= 0:
        return {
            "dailyLimit": 0.00,
            "remainingBudget": remaining_budget,
            "remainingDays": remaining_days,
            "status": "over",
            "message": "You have spent your full budget (not counting your reserve).",
        }

    # Round down to the cent so the user never goes over by following the number
    daily_limit = math.floor(remaining_budget / remaining_days * 100) / 100

    if remaining_budget <= WARNING_THRESHOLD * total_budget:
        status, message = "warning", "20% or less of your budget is left."
    else:
        status, message = "ok", "You are on track with your budget."

    return {
        "dailyLimit": daily_limit,
        "remainingBudget": remaining_budget,
        "remainingDays": remaining_days,
        "status": status,
        "message": message,
    }


@app.route("/daily-limit", methods=["POST"])
def daily_limit():
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    data = request.get_json(silent=True)

    try:
        result = calculate_daily_limit(*parse_request(data))
    except ValidationError as e:
        return jsonify({"error": str(e), "correlationId": correlation_id}), 400
    except Exception:
        # Log the real error server-side; don't leak internals to the caller
        app.logger.exception("Unexpected error (correlationId=%s)", correlation_id)
        return jsonify({"error": "Internal server error", "correlationId": correlation_id}), 500

    result["correlationId"] = correlation_id
    return jsonify(result)


if __name__ == "__main__":
    # Local only and debug off by default. Set FLASK_DEBUG=1 while developing.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG") == "1"
    print(f"Daily Spending Limit Calculator running at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
