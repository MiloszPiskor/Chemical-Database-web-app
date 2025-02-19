import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
import logging
from flask import has_request_context, request, jsonify, abort

from werkzeug.exceptions import NotFound, HTTPException

# Add the directory containing 'models.py' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
patch('utils.requires_auth', lambda x: x).start()
# patch('utils.validate_company_data', lambda data, is_update, company_instance: None).start()
from companies import User, Company, get_company, get_companies, edit_company
from models import Company, User

class TestCompaniesModels:

    @pytest.mark.parametrize(
        "mock_company_data, response_keyword, expected_status_code",
        [
            # Scenario 1: Valid Company
            ({"address": "Mock Address","contact_number": "123456789","contact_person": "Mock Contact Person","id": 1,"name": "Mock Company","user_id": 1},
             "company",
             200),

            # Scenario 2: Invalid Company(no data)
            (None, "error", 404),
        ])
    @patch('companies.db.get_or_404')
    def test_get_company(self, mock_get_or_404, mock_company_data, response_keyword, expected_status_code, app):
        """Test the get_company function in companies.py"""

        if mock_company_data is not None:
            mock_company = MagicMock(spec=Company)
            # Set attributes dynamically
            for key, value in mock_company_data.items():
                setattr(mock_company, key, value)

            mock_get_or_404.return_value = mock_company

            # Ensure to_dict() returns a real dictionary
            mock_company.to_dict.return_value = mock_company_data
        else:
            mock_get_or_404.side_effect = NotFound()

        with app.app_context():
            with app.test_request_context():

                response = get_company(1)

        response_data = response[0].json
        status_code = response[1]
        print(f"Response: {response_data}. Status: {status_code}")

        assert status_code == expected_status_code
        if status_code == 200:
            assert response_keyword in response_data
            assert response_data["company"]["name"] == mock_company_data["name"]
            assert response_data["company"]["address"] == mock_company_data["address"]
            assert response_data["company"]["contact_person"] == mock_company_data["contact_person"]
            assert response_data["company"]["contact_number"] == mock_company_data["contact_number"]
        else:
            assert response_keyword in response_data

    @pytest.mark.parametrize(
        "mock_company_data, expected_company_count, expected_status_code",
        [
            # Scenario 1: Valid Companies
            ([
                {"address": "Mock Address","contact_number": "123456789","contact_person": "Mock Contact Person","id": 1,"name": "Mock Company","user_id": 1},
                {"address": "Mock Address 2","contact_number": "987654321","contact_person": "Mock Contact Person 2","id": 2,"name": "Mock Company 2","user_id": 1}
            ],
             2,
             200),

            # Scenario 2: Empty Companies
            ([], 0, 200),
        ])
    @patch('companies.User.query')
    def test_get_companies(self, mock_query, mock_company_data, expected_company_count, expected_status_code,  app):
        """Test the get_companies function in companies.py"""

        # Prepare the mock companies list
        mock_companies = []
        for company_data in mock_company_data:
            mock_company = MagicMock(spec=Company, **company_data)
            mock_company.to_dict.return_value = company_data
            mock_companies.append(mock_company)

        with app.app_context():
            with app.test_request_context():

                response = get_companies()

        response_data = response[0].json
        status_code = response[1]

        print(f"Response: {response_data}. Status: {status_code}")
        print(f"Current length of companies list: {len(response_data)}")
        print(f"Expected company count: {expected_company_count}")

        # Assertions

        assert status_code == expected_status_code
        assert len(response_data) == expected_company_count

        if status_code == 200:
            for i, company in enumerate(response_data):
                assert company["name"] == mock_company_data[i]["name"]
                assert company["address"] == mock_company_data[i]["address"]
                assert company["contact_person"] == mock_company_data[i]["contact_person"]
                assert company["contact_number"] == mock_company_data[i]["contact_number"]
        else:
            assert response_data == []

    @pytest.mark.parametrize(
        "mock_company_data, mock_request_data,  validation_return, expected_status_code, expected_response",
        [
            # Scenario 1: Valid PATCH JSON payload
            ({"address": "Mock Address","contact_number": "123456789","contact_person": "Mock Contact Person","id": 1,"name": "Mock Company","user_id": 1},
             {"address": "Mock Address","contact_number": "123456211","contact_person": "Mock Contact Person 2", "name": "Mock Company 2"}, None, 200,
             {"address": "Mock Address", "contact_number": "123456211", "contact_person": "Mock Contact Person 2",
              "id": 1, "name": "Mock Company 2", "user_id": 1}),

            # Scenario 2: Invalid PATCH JSON payload (empty)
            ({"address": "Mock Address","contact_number": "123456789","contact_person": "Mock Contact Person","id": 1,"name": "Mock Company","user_id": 1},
             None, "The following fields cannot be empty: name, address, contact_person, contact_number.", 400,
             {"error" : "The following fields cannot be empty: name, address, contact_person, contact_number."}),

            # Scenario 3: Invalid PATCH JSON payload (name already exists)
            ({"address": "Mock Address","contact_number": "123456789","contact_person": "Mock Contact Person","id": 1,"name": "Mock Company","user_id": 1},
                {"address": "Mock Address","contact_number": "123456211","contact_person": "Mock Contact Person 2", "name": "Mock Company 2"}, "Company with the name: Mock Company 2 already exists.", 400,
                {"error" : "Company with the name: Mock Company 2 already exists."}),

            # Scenario 4: Invalid PATCH JSON payload (company doesn't exist- Invalid ID)
            (None, {"address": "Mock Address","contact_number": "123456211","contact_person": "Mock Contact Person 2", "name": "Mock Company 2"},
             "Unauthorized or company not found!", 404, {"error" : "Unauthorized or company not found!"}),
        ])
    @patch('companies.validate_company_data')
    @patch('companies.get_user_item_or_404')
    @patch('companies.db.session.commit')
    def test_edit_company(self, mock_commit, mock_get_user_item_or_404, mock_validate_company_data, mock_company_data, mock_request_data, validation_return, expected_status_code, expected_response, app):
        """Test the edit_company function in companies.py"""
        # Mock the company object returned by the helper

        if mock_company_data is not None:
            company_instance = MagicMock(spec_set=Company, **mock_company_data)

            def dynamic_to_dict():  # Dynamically return a dictionary based on the object's attributes
                return {column: getattr(company_instance, column) for column in mock_company_data.keys()}

            company_instance.to_dict.side_effect = dynamic_to_dict
            mock_get_user_item_or_404.return_value = company_instance

        else:

            mock_get_user_item_or_404.side_effect = NotFound("Unauthorized or company not found!") # Simulate a 404 error

        # Mock the validation function (simulate validation failure or success):::: test of this function is in test_utils.py
        mock_validate_company_data.return_value = validation_return

        with app.app_context():
            with app.test_request_context(json=mock_request_data):
                with patch.object(request, "get_json",
                                  return_value=mock_request_data) as mock_get_json:  # Mock the request data
                    logging.debug(f"Request context active inside: {has_request_context()}")

                    if mock_company_data is None:  # Expecting a 404 (company not found)
                        with pytest.raises(NotFound) as excinfo:
                            edit_company(1)

                        response = app.handle_user_exception(excinfo.value)

                        assert isinstance(response, NotFound) # Check if the response is a 404 error
                        mock_validate_company_data.assert_not_called()
                        mock_commit.assert_not_called()

                    else:
                        # Normal execution of `edit_company`
                        response = edit_company(1)

                        response_data, status_code = response

                        response_data = response_data.json
                        status_code = status_code

                        # Assertions
                        assert status_code == expected_status_code
                        assert response_data == expected_response

                        if expected_status_code == 200:
                            mock_get_user_item_or_404.assert_called_once()
                            mock_validate_company_data.assert_called_once()
                            mock_commit.assert_called_once()

                        elif expected_status_code == 400:
                            mock_get_user_item_or_404.assert_called_once()
                            mock_validate_company_data.assert_called_once()
                            mock_commit.assert_not_called()






