"""Unit tests for the Daily Spending Limit Calculator.

Run with:  python -m unittest -v
These use Flask's test client, so the server does not need to be running.
"""

import unittest
from datetime import date

from app import app, calculate_daily_limit


def body(**overrides):
    data = {
        "totalBudget": 2000.00,
        "reserve": 300.00,
        "expenses": [
            {"date": "2025-05-01", "amount": 500.00},
            {"date": "2025-05-05", "amount": 120.50},
        ],
        "endDate": "2025-05-31",
        "currentDate": "2025-05-07",
    }
    data.update(overrides)
    return data


class CalculateDailyLimitTests(unittest.TestCase):
    def test_on_track(self):
        r = calculate_daily_limit(2000, 300, 620.5, date(2025, 5, 7), date(2025, 5, 31))
        self.assertEqual(r["remainingBudget"], 1079.5)
        self.assertEqual(r["remainingDays"], 25)
        self.assertEqual(r["dailyLimit"], 43.18)  # 43.18 per day, rounded down
        self.assertEqual(r["status"], "ok")

    def test_rounds_down_to_the_cent(self):
        r = calculate_daily_limit(100, 0, 0, date(2025, 5, 1), date(2025, 5, 3))
        self.assertEqual(r["dailyLimit"], 33.33)  # never 33.34

    def test_last_day_counts_as_one_day(self):
        r = calculate_daily_limit(100, 0, 40, date(2025, 5, 31), date(2025, 5, 31))
        self.assertEqual(r["remainingDays"], 1)
        self.assertEqual(r["dailyLimit"], 60.0)

    def test_warning_at_twenty_percent(self):
        r = calculate_daily_limit(1000, 0, 800, date(2025, 5, 1), date(2025, 5, 10))
        self.assertEqual(r["status"], "warning")

    def test_overspent_never_returns_negative_limit(self):
        r = calculate_daily_limit(2000, 300, 3000, date(2025, 5, 7), date(2025, 5, 31))
        self.assertEqual(r["dailyLimit"], 0.0)
        self.assertEqual(r["remainingBudget"], -1300.0)
        self.assertEqual(r["status"], "over")

    def test_period_ended(self):
        r = calculate_daily_limit(2000, 0, 0, date(2025, 6, 1), date(2025, 5, 31))
        self.assertEqual(r["remainingDays"], 0)
        self.assertEqual(r["status"], "ended")


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, data, **kwargs):
        return self.client.post("/daily-limit", json=data, **kwargs)

    def test_happy_path(self):
        resp = self.post(body(), headers={"X-Correlation-ID": "abc-123"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["dailyLimit"], 43.18)
        self.assertEqual(resp.json["correlationId"], "abc-123")

    def test_generates_correlation_id_when_missing(self):
        resp = self.post(body())
        self.assertTrue(resp.json["correlationId"])

    def test_missing_field(self):
        data = body()
        del data["totalBudget"]
        resp = self.post(data)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("totalBudget", resp.json["error"])

    def test_bad_values_return_400_not_500(self):
        bad_inputs = [
            body(totalBudget="abc"),
            body(totalBudget=True),
            body(reserve=-5),
            body(reserve=5000),
            body(expenses="nope"),
            body(expenses=[{"date": "2025-05-01"}]),
            body(expenses=[{"amount": "12"}]),
            body(endDate="05/31/2025"),
            body(currentDate=20250507),
        ]
        for data in bad_inputs:
            with self.subTest(data=data):
                resp = self.post(data)
                self.assertEqual(resp.status_code, 400)
                self.assertIn("error", resp.json)

    def test_non_json_body(self):
        resp = self.client.post("/daily-limit", data="hello", content_type="text/plain")
        self.assertEqual(resp.status_code, 400)

    def test_empty_expenses(self):
        resp = self.post(body(expenses=[]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["remainingBudget"], 1700.0)


if __name__ == "__main__":
    unittest.main()
