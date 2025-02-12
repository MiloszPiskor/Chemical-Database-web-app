from unittest.mock import patch
import sys
import os

# Add the directory containing 'validator_funcs.py' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

import pytest
from flask import Flask, jsonify
from validator_funcs import (
    validate_json_payload,
    validate_document_nr,
    validate_transaction_type,
    validate_date_format,
    validate_line_items,
)

@pytest.fixture
def app():
    """App fixture to register the routes."""
    app = Flask(__name__)
    app.testing = True

    # Mock view function that uses all 7 validators
    @app.route("/mock-endpoint", methods=["POST"])
    def mock_view_function(*args, **kwargs):
        data = kwargs.get('data')
        return jsonify(success=True, data=data), 200

    return app

@pytest.fixture
def client(app):
    """Test client fixture."""
    return app.test_client()

class TestEntryValidators:

    @classmethod
    @pytest.mark.skip
    def setup_class(cls):
        """Setup of the reusable data for the test"""
        cls.valid_entry = {
    "date" : "2025-02-07",
    "document_nr" : "WZ 7/01/2025",
    "transaction_type" : "Purchase",
    "company": "TaoO'Clock",
    "line_items" : [
        {"quantity" : 48,
        "price_per_unit" : 12,
        "product" : "Zep 45"},
        {"quantity" : 36,
        "price_per_unit" : 13,
        "product" : "Big Orange"}
    ]
}

    @pytest.mark.parametrize(
    "json_payload, expected_status, expected_response",
    [
        (  # Valid payload test
                {
                    "date": "2025-02-07",
                    "document_nr": "WZ 7/01/2025",
                    "transaction_type": "Purchase",
                    "company": "TaoO'Clock",
                    "line_items": [
                        {"quantity": 48,
                         "price_per_unit": 12,
                         "product": "Zep 45"},
                        {"quantity": 36,
                         "price_per_unit": 13,
                         "product": "Big Orange"}
                    ]
                },
            200,
            {"success": True, "data": {
                    "date": "2025-02-07",
                    "document_nr": "WZ 7/01/2025",
                    "transaction_type": "Purchase",
                    "company": "TaoO'Clock",
                    "line_items": [
                        {"quantity": 48,
                         "price_per_unit": 12,
                         "product": "Zep 45"},
                        {"quantity": 36,
                         "price_per_unit": 13,
                         "product": "Big Orange"}
                    ]
                }}
        ),
        (  # Missing JSON test
            None,
            400,
            {"error": "No JSON data found in the request body."}
        ),
        (  # Invalid fields test
                {
                    "date": "2025-02-07",
                    "document_nr": "WZ 7/01/2025",
                    "extra_field" : "invalid data",
                    "transaction_type": "Purchase",
                    "company": "TaoO'Clock",
                    "line_items": [
                        {"quantity": 48,
                         "price_per_unit": 12,
                         "product": "Zep 45"},
                        {"quantity": 36,
                         "price_per_unit": 13,
                         "product": "Big Orange"}
                    ]
                },
            400,
            {"error": "Invalid field(s): extra_field while trying to create a new entry."}
        ),
        (# Missing fields test
                {
                    "date": "2025-02-07",
                    "document_nr": "WZ 7/01/2025",
                    "transaction_type": "Purchase",
                    "line_items": [
                        {"quantity": 48,
                         "price_per_unit": 12,
                         "product": "Zep 45"},
                        {"quantity": 36,
                         "price_per_unit": 13,
                         "product": "Big Orange"}
                    ]
                },
                400,
                {"error" : "Missing field(s): company while trying to create a new entry."}

        )
    ],
)
    def test_validate_json_payload(self, client, json_payload, expected_status, expected_response, app):
        """Ensure the given json payload in the request body is relevant (request body contains only required fields)"""

        print("Registered view functions:", app.view_functions.keys())  # Debugging step

        view_function = app.view_functions.get("mock_view_function")

        # Apply the decorator to the view function:
        view_function = validate_json_payload(view_function)
        # Register the decorated view function back into the app:
        app.view_functions["mock_view_function"] = view_function
        # Send a request with the payload:
        if json_payload is not None:
            response = client.post("/mock-endpoint", json=json_payload)
        else:
            response = client.post("/mock-endpoint", json={})

        # Assertions:
        assert response.status_code == expected_status
        assert response.json == expected_response

    @pytest.mark.parametrize("json_payload, expected_status, expected_response",
        [
        # Valid payload test
        ({"document_nr" : "WZ 8/08/2025"}, 200, {"success" : True, "data" : {"document_nr" : "WZ 8/08/2025"}}),
        # Empty payload test
        (None, 400, {"error" : "Document number is required."}),
        # Invalid payload test
            ({"document_nr" : "-1-08-2025"}, 400, {
                "error": "Invalid document number format: -1-08-2025. The accepted format example"
                " for document nr.: 'WZ 123/02/2025', meaning: WZ (document nr)/(month)/year)."})
        ]
    )
    def test_validate_document_number(self, client, app, json_payload, expected_status, expected_response):
        """Ensure the provided WZ document number is of a correct format"""
        with app.app_context():
            view_function = app.view_functions.get("mock_view_function")
            decorated_function = validate_document_nr(view_function)

            app.view_functions["mock_view_function"] = view_function
            # Extract data in a way that simulates the real function call
            # Send a request with the payload (empty dict if no data provided):
            if json_payload is None:
                response, status_code = decorated_function(data={})
            else:
                response, status_code = decorated_function(data=json_payload)
            response_json = response.get_json()

            # Assertions:
            assert status_code == expected_status
            assert response_json == expected_response

    @pytest.mark.parametrize("json_payload, expected_status, expected_response",
        [
        # Valid payload test
        ({"transaction_type" : "Purchase"}, 200, {"success" : True, "data" : {"transaction_type" : "Purchase"}}),
        # Empty payload test - UNNECESSARY DUE TO 1ST VALIDATOR TAKING CARE OF ANY MISSING FIELDS
        # Invalid payload test
            ({"transaction_type" : "Sopply"}, 400, {
                "error": "Invalid data in the 'transaction type' field. Should be Purchase or Supply."})
        ]
    )
    def test_validate_transaction_type(self, client, app, json_payload, expected_status, expected_response):

        with app.app_context():
            view_function = app.view_functions.get("mock_view_function")
            decorated_function = validate_transaction_type(view_function)

            app.view_functions["mock_view_function"] = view_function
            response, status_code = decorated_function(data=json_payload)
            response_json = response.get_json()

            # Assertions:
            assert status_code == expected_status
            assert response_json == expected_response

    @pytest.mark.parametrize("json_payload, expected_status, expected_response",
    [
    # Valid payload test
    ({"date" : "2025-02-07"}, 200, {"success" : True, "data" : {"date" : "2025-02-07"}}),
    # Invalid payload test
    ({"date" : "2025/02/07"}, 400, {"error": "Invalid date format: 2025/02/07 while adding new entry. The accepted date format is ISO 8601, meaning: YYYY-MM-DD"}),
    # Invalid payload test
    ({"date": "202/02/07"}, 400, {"error": "Invalid date format: 202/02/07 while adding new entry. The accepted date format is ISO 8601, meaning: YYYY-MM-DD"})
    ])
    def test_validate_date_format(self, client, app, json_payload, expected_status, expected_response):

        with app.app_context():
            view_function = app.view_functions.get("mock_view_function")
            decorated_function = validate_date_format(view_function)

            app.view_functions["mock_view_function"] = view_function
            response, status_code = decorated_function(data=json_payload)
            response_json = response.get_json()

            # Assertions:
            assert status_code == expected_status
            assert response_json == expected_response

    @pytest.mark.parametrize("json_payload, expected_status, expected_response",
    [    # Invalid payload test (extra field(s))
    ({"line_items" : [
        {"quantity" : 36,
        "something" : "blah blah",
        "price_per_unit" : 12,
        "product" : "Zep 45"},
        {"quantity" : 36,
        "price_per_unit" : 13,
        "product" : "Big Orange"}
    ]}, 400, {"error": "Invalid field(s): something while trying to create new LineItem."}),
    # Invalid payload test (missing fields)
    ({"line_items" : [
        {"quantity" : 36,
        "product" : "Zep 45"},
        {"quantity" : 36,
        "price_per_unit" : 13,
        "product" : "Big Orange"}
    ]}, 400, {"error": "Missing field(s): price_per_unit while trying to create new LineItem."}),
    # Invalid payload test (negative values for price or quantity)
    ({"line_items" : [
        {"quantity" : -36,
         "price_per_unit": 12,
        "product" : "Zep 45"},
        {"quantity" : 36,
        "price_per_unit" : -13,
        "product" : "Big Orange"}
    ]}, 400, {"error": "Non-positive values for price or quantity for the product in the new Entry."}),
    # Invalid payload test (missing multiple fields: product, quantity)
    ({"line_items" : [
        {"price_per_unit": 180},
        {"quantity" : 36,
        "price_per_unit" : 120,
        "product": "Big Orange"}
    ]}, 400, {"error": "Missing field(s): quantity, product while trying to create new LineItem."})
    ])
    def test_validate_line_items(self, client, app, json_payload, expected_status, expected_response):

        with app.app_context():
            view_function = app.view_functions.get("mock_view_function")
            decorated_function = validate_line_items(view_function)

            app.view_functions["mock_view_function"] = view_function
            response, status_code = decorated_function(data=json_payload)
            response_json = response.get_json()

            # Assertions:
            assert status_code == expected_status
            assert response_json == expected_response

# @pytest.mark.parametrize("payload, expected_status_code, expected_error", [
#     ({"name": "Test Entry", "value": 100}, 201, None),  # Valid payload
#     ({"name": "Test Entry"}, 400, "Invalid field(s): value"),  # Missing "value"
#     ({"name": "Test Entry", "extra_field": "test"}, 400, "Invalid field(s): extra_field"),  # Extra field
#     ({"value": 100}, 400, "Invalid field(s): name"),  # Missing "name"
#     (None, 400, "No JSON data found in the request body."),  # No JSON body
# ])
# def test_validate_json_payload(client, payload, expected_status_code, expected_error):
#     # If no payload is provided, mock the request to return None
#     if payload is None:
#         with patch("flask.request.get_json", return_value=None):
#             response = client.post("/create-entry")
#     else:
#         response = client.post("/create-entry", json=payload)
#
#     assert response.status_code == expected_status_code
#
#     if expected_error:
#         assert response.json["error"] == expected_error
#     else:
#         assert response.json["message"] == "Entry created successfully"
#         assert response.json["data"] == payload