import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import current_app
from werkzeug.exceptions import NotFound

# Add the directory containing 'models.py' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
patch('utils.requires_auth', lambda x: x).start()

from entries import get_entry, get_entries
from models import Entry, User


class TestEntryModels:

    @pytest.mark.parametrize(
        "mock_entry_data, response_keyword, expected_status_code",
        [
            # Scenario 1: Valid return (existing ID)
            (
                    {
                        "company_id": 2,
                        "date": "2024-02-07",
                        "document_nr": "WZ 10/01/2025",
                        "id": 1,
                        "line_items": [
                            {
                                "id": 1,
                                "price_per_unit": 13.0,
                                "product_id": 1,
                                "quantity": 12.0
                            },
                            {
                                "id": 2,
                                "price_per_unit": 13.0,
                                "product_id": 2,
                                "quantity": 36.0
                            }
                        ],
                        "transaction_type": "Purchase",
                        "user_id": 1
                    },
                    "entry",
                    200
            ),

            # Scenario 2: Invalid return (non-existing ID) 404 Error
            (
                    None,
                    "error",
                    404
            ),
        ]
    )
    @patch('entries.get_user_item_or_404')
    def test_get_entry(self, mock_get_or_404, mock_entry_data, response_keyword, expected_status_code, app):
        """Test the get_entry function in entries.py properly isolated to only
        reflect a business logic: without a real db or http calls"""

        if mock_entry_data is not None:
            # Create a mock Entry object with the provided data
            mock_entry = MagicMock(spec_set=Entry, **mock_entry_data)

            # Define a dynamic to_dict method for the mock Entry object
            def dynamic_to_dict():
                return {column: getattr(mock_entry, column) for column in mock_entry_data.keys()}

            # Set the side effect of the to_dict method to the dynamic function
            mock_entry.to_dict.side_effect = dynamic_to_dict
            mock_get_or_404.return_value = mock_entry

        else:
            # Simulate a NotFound exception for invalid entry ID
            mock_get_or_404.side_effect = NotFound(description="Unauthorized or entry not found!")

        with app.app_context():
            with app.test_request_context():
                # Call the get_entry function
                response = get_entry(1)

        # Unpack the response data and status code
        response_data = response[0].json
        status_code = response[1]

        # Log the response data and status code
        current_app.logger.info(f"Response: {response_data}. Status: {status_code}")

        # Assertions
        assert status_code == expected_status_code
        assert response_keyword in response_data
        if status_code == 200:
            assert response_data == {"entry": mock_entry_data}

    @pytest.mark.parametrize(
        "mock_entry_data, response_keyword, expected_status_code, expected_entry_count",
        [
            # Scenario 1: Valid return with multiple entries
            (
                    [
                        {
                            "company_id": 2,
                            "date": "2024-02-07",
                            "document_nr": "WZ 10/01/2025",
                            "id": 1,
                            "line_items": [
                                {"id": 1, "price_per_unit": 13.0, "product_id": 1, "quantity": 12.0},
                                {"id": 2, "price_per_unit": 13.0, "product_id": 2, "quantity": 36.0}
                            ],
                            "transaction_type": "Purchase",
                            "user_id": 1
                        },
                        {
                            "company_id": 1,
                            "date": "2024-02-07",
                            "document_nr": "WZ 1/01/2025",
                            "id": 2,
                            "line_items": [
                                {"id": 3, "price_per_unit": 13.0, "product_id": 1, "quantity": 12.0},
                                {"id": 4, "price_per_unit": 13.0, "product_id": 2, "quantity": 36.0}
                            ],
                            "transaction_type": "Purchase",
                            "user_id": 1
                        },
                        {
                            "company_id": 1,
                            "date": "2024-02-07",
                            "document_nr": "WZ 2/01/2025",
                            "id": 3,
                            "line_items": [
                                {"id": 5, "price_per_unit": 13.0, "product_id": 1, "quantity": 120.0},
                                {"id": 6, "price_per_unit": 13.0, "product_id": 2, "quantity": 48.0}
                            ],
                            "transaction_type": "Purchase",
                            "user_id": 1
                        }
                    ],
                    "entries",
                    200,
                    3
            ),
            # Scenario 2: Valid return with no entries
            ([], "entries", 200, 0),
            # Scenario 3: Invalid return (server error)
            (Exception("Database connection failed"), "error", 500, 0),
        ]
    )
    @patch('entries.g')
    def test_get_entries(self, mock_g, mock_entry_data, response_keyword, expected_status_code, expected_entry_count, app):
        """Test of get_entries function in entries.py"""

        mock_user = MagicMock(spec=User, id=1)

        if isinstance(mock_entry_data, list):
            mock_entries = [MagicMock(spec=Entry, **entry_data) for entry_data in mock_entry_data] # Prepare the mock entries list
            for mock_entry, entry_data in zip(mock_entries, mock_entry_data):
                mock_entry.to_dict.side_effect = lambda: {key: getattr(mock_entry, key) for key in entry_data.keys()}

            mock_user.entries = mock_entries
        # Simulating a Server Error by raising an Exception
        else:
            mock_user.entries = MagicMock(side_effect=Exception("Database connection failed"))

        mock_g.user = mock_user  # Mock g.user to return a valid user

        with app.app_context():
            with app.test_request_context():
                response = get_entries()

        response_data = response[0].json
        status_code = response[1]

        print(f"Response: {response_data}. Status: {status_code}")
        print(f"Current length of companies list: {len(response_data)}")
        print(f"Expected company count: {expected_entry_count}")

        # Assertions

        assert status_code == expected_status_code, f"Expected status {expected_status_code}, got {status_code}"
        assert len(
            response_data) == expected_entry_count, f"Expected {expected_entry_count} companies, got {len(response_data)}"

        if status_code == 200 and expected_entry_count == 3:
            assert response_data == mock_entry_data
        elif status_code == 200 and expected_entry_count == 0:
            assert response_data == []
        elif status_code == 500:
            assert "error" in response_data
