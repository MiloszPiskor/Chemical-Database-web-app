import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import logging
from flask import has_request_context, request

from werkzeug.exceptions import NotFound

# Add the directory containing 'models.py' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from companies import User, Company, get_company, get_companies
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


