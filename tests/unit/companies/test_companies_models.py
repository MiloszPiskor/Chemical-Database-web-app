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
from companies import User, Company, get_company, get_companies, edit_company, delete_company, add_company
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
    @patch('companies.get_user_item_or_404')
    def test_get_company(self, mock_get_or_404, mock_company_data, response_keyword, expected_status_code, app):
        """Test the get_company function in companies.py"""

        if mock_company_data is not None:
            mock_company = MagicMock(spec_set=Company, **mock_company_data)

            mock_get_or_404.return_value = mock_company

            # Ensure to_dict() returns a real dictionary
            mock_company.to_dict.return_value = mock_company_data
        else:
            mock_get_or_404.side_effect = NotFound(description="Unauthorized or company not found!")

        with app.app_context():
            with app.test_request_context():

                response = get_company(1)

        response_data = response[0].json
        status_code = response[1]
        print(f"Response: {response_data}. Status: {status_code}")

        assert status_code == expected_status_code
        assert response_keyword in response_data
        if status_code == 200:
            assert response_data == {"company" : mock_company_data}

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
    @patch('companies.g')
    def test_get_companies(self, mock_g, mock_company_data, expected_company_count, expected_status_code,  app):
        """Test the get_companies function in companies.py properly isolated to only
        reflect a business logic: without a real db or http calls"""

        # Prepare the mock companies list
        mock_companies = []
        for company_data in mock_company_data:
            mock_company = MagicMock(spec=Company, **company_data)
            mock_company.to_dict.return_value = company_data
            mock_companies.append(mock_company)

        mock_user = MagicMock(spec=User, id= mock_company_data[0].get('user_id') if mock_company_data else 1 , companies = mock_companies)
        mock_g.user = mock_user  # Mock g.user to return a valid user

        with app.app_context():
            with app.test_request_context():

                response = get_companies()

        response_data = response[0].json
        status_code = response[1]

        print(f"Response: {response_data}. Status: {status_code}")
        print(f"Current length of companies list: {len(response_data)}")
        print(f"Expected company count: {expected_company_count}")

        # Assertions

        assert status_code == expected_status_code, f"Expected status {expected_status_code}, got {status_code}"
        assert len(
            response_data) == expected_company_count, f"Expected {expected_company_count} companies, got {len(response_data)}"

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

            mock_get_user_item_or_404.side_effect = NotFound(description=validation_return) # Simulate a 404 error

        # Mock the validation function (simulate validation failure or success):::: test of this function is in test_utils.py
        mock_validate_company_data.return_value = validation_return

        with app.app_context():
            with app.test_request_context(json=mock_request_data):
                with patch.object(request, "get_json",
                                  return_value=mock_request_data) as mock_get_json:  # Mock the request data
                    logging.debug(f"Request context active inside: {has_request_context()}")

                    response = edit_company(1)

                    # Check if response is a tuple (manual JSON response) or a Flask Response object
                    if isinstance(response,tuple): # Unpack tuple manually
                        response_data = response[0].json # Unpack the response
                        status_code = response[1] # Unpack the status code
                    else:

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

        elif expected_status_code == 404:
            assert status_code == expected_status_code
            assert response_data == {"error": "Unauthorized or company not found!"}
            mock_get_user_item_or_404.assert_called_once()
            mock_validate_company_data.assert_not_called()
            mock_commit.assert_not_called()

    @pytest.mark.parametrize(
        "mock_company_data, response_keyword, expected_status_code",
        [
            # Scenario 1: Valid Product Delete
            ({"address": "Mock Address","contact_number": "123456789","contact_person": "Mock Contact Person","id": 1,"name": "Mock Company","user_id": 1},
             "success", 200),

            # Scenario 2: Invalid Product Delete (Product not found)
            (None, "error", 404),

        ])
    @patch('companies.get_user_item_or_404')
    @patch('companies.db.session.commit')
    @patch('companies.db.session.delete')
    def test_delete_company(self, mock_delete, mock_commit, mock_get_or_404, mock_company_data, response_keyword, expected_status_code, app):
        """Unit test for deleting a company without a real DB."""
        if mock_company_data is not None:
            mock_company = MagicMock(spec=Company, **mock_company_data)

            mock_get_or_404.return_value = mock_company
        else:
            mock_get_or_404.side_effect = NotFound(description="Successfully deleted the company: Mock Company.")

        with app.app_context():
            with app.test_request_context():
                result = delete_company(1)

        response_data = result[0].json
        status_code = result[1]
        print(f"{response_data}: RESPONSE DATA")

        print(
            f"MOCK FUNC COUNT:{mock_get_or_404.call_count}, CALL ARGS: {mock_get_or_404.call_args}, {mock_get_or_404.method_calls}.")

        # Assertions
        assert status_code == expected_status_code
        assert response_keyword in response_data
        mock_get_or_404.assert_called_once_with(Company,
                                                1)

        if status_code == 200:
            mock_delete.assert_called_once_with(mock_company)  # Ensure db.session.delete was called
            mock_commit.assert_called_once()  # Ensure db.session.commit was called
        else:
            assert response_data[response_keyword] == "Successfully deleted the company: Mock Company."
            mock_delete.assert_not_called()
            mock_commit.assert_not_called()

    @pytest.mark.parametrize(
        "mock_company_data, mock_request_data, validation_return, expected_status_code, expected_response",
        [
            # Scenario 1: Valid Company
            (
            {"address": "Mock Address", "contact_number": "123456789", "contact_person": "Mock Contact Person", "id": 1,
             "name": "Mock Company", "user_id": 1},
            {"address": "Mock Address", "contact_number": "123456789", "contact_person": "Mock Contact Person",
             "name": "Mock Company"}, None, 200,
            {'success': "Successfully created a new company: Mock Company!"}),

            # Scenario 2: Invalid Company (missing field(s))
            (
            {"address": "Mock Address", "contact_number": "123456789", "contact_person": "Mock Contact Person", "id": 1,
             "name": "Mock Company", "user_id": 1},
            {"contact_number": "123456789", "contact_person": "Mock Contact Person", "name": "Mock Company"},
            "The following fields cannot be empty: address.", 400,
            {"error": "The following fields cannot be empty: address."}),

            # Scenario 3: Invalid Company (name already exists)
            (
            {"address": "Mock Address", "contact_number": "123456789", "contact_person": "Mock Contact Person", "id": 1,
             "name": "Mock Company", "user_id": 1},
            {"address": "Mock Address", "contact_number": "123456789", "contact_person": "Mock Contact Person",
             "name": "Existing Company"}, "This name is already occupied by another Company.", 400,
            {"error": "This name is already occupied by another Company."}),

            # Scenario 4: Invalid Company (invalid field(s))
            (
            {"address": "Mock Address", "contact_number": "123456789", "contact_person": "Mock Contact Person", "id": 1,
             "name": "Mock Company", "user_id": 1},
            {"address": "Mock Address", "contact_number": "123456789", "contact_person": "Mock Contact Person",
             "name": "Mock Company", "extra_field": "Extra"}, "Invalid field(s): extra_field", 400,
            {"error": "Invalid field(s): extra_field"}),
        ])
    @patch('companies.db.session.commit')
    @patch('companies.db.session.add')
    @patch('companies.validate_company_data')
    @patch('companies.Company')
    @patch('companies.g')
    def test_add_company(self, mock_g, mock_new_company, mock_validate, mock_add, mock_commit, mock_company_data, mock_request_data, validation_return, expected_status_code,
                         expected_response, app):
        """Unit test for adding a company without a real DB or HTTP calls - fully isolated to reflect only business logic"""

        mock_company = MagicMock(spec=Company, **mock_company_data)  # Mock the company object
        mock_new_company.result_value = mock_company  # Set the return value of new_company to the mock company

        mock_user = MagicMock(spec=User, id=mock_company_data['user_id'])
        mock_g.user = mock_user  # Mock g.user to return a valid user

        mock_validate.return_value = validation_return  # Mock the validation function
        with app.app_context():
            with app.test_request_context(json=mock_request_data):  # Mock the request data
                with patch.object(request, "get_json",
                                  return_value=mock_request_data) as mock_get_json:  # Mock the request data
                    logging.debug(f"Request context active inside: {has_request_context()}")

                    result = add_company()  # Add company

        response_data = result[0].json
        status_code = result[1]

        print(f"Response: {response_data}, status code: {status_code}")

        # Assertions
        assert status_code == expected_status_code
        assert response_data == expected_response
        mock_validate.assert_called_once()  # Ensure validate_company_data was called

        if expected_status_code == 200:
            mock_add.assert_called_once()  # Ensure db.session.add was called
            mock_commit.assert_called_once()  # Ensure db.session.commit was called
        elif expected_status_code == 400:
            mock_add.assert_not_called()
            mock_commit.assert_not_called()








