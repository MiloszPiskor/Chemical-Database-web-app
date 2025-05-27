import pytest
import sys
import os
import copy
from unittest.mock import patch, MagicMock
import logging
from flask import has_request_context, request
from werkzeug.exceptions import NotFound
from models import Product, Company

def get_user_item_or_404_side_effect(model_class, item_id):

    if model_class == Company:

        if mock_company:
            return MagicMock(spec_set=Company, **mock_company)
        else:
            raise NotFound(description="Unauthorized or company not found!")

    elif model_class == Product:

        if mock_product:
            return MagicMock(spec_set=Product, **mock_product)
        else:
            raise NotFound(description="Unauthorized or product not found!")

patch('utils.requires_auth', lambda x: x).start()


class TestAnalyticsModels:

    @pytest.fixture
    def mock_date_range(self, request):
        if request.param == "valid":
            return {
                "start": "2024-01-01",
                "end": "2024-01-31"
            }
        elif request.param == "invalid":
            return {"ValueError": "Start date must be earlier than or equal to end date."}

    @pytest.fixture
    def mock_product(self, request):
        if request.param == "valid":
            return {"id": 1, "name": "Mock Product"}
        elif request.param == "invalid":
            return None

    @pytest.fixture
    def mock_company(self, request):
        if request.param == "valid":
            return {"id": 2, "name": "Mock Company"}
        elif request.param == "invalid":
            return None

    @pytest.mark.parametrize(
        "mock_date_range, mock_product_id, mock_company_id, mock_company, mock_product,"
        "mock_entry_totals_data, expected_response, expected_response_code",
        [
            (
                "valid",         # mock_date_range
                "1",             # product_id
                "2",             # company_id
                "valid",         # mock_company
                "valid",         # mock_product
                {"supply": 1200, "purchase": 600},  # mock_entry_totals_data
                {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "monetary_totals": {
                        "filters": {
                            "company": {"id": 2, "name": "Mock Company"},
                            "product": {"id": 1, "name": "Mock Product"}
                        },
                        "supply": 1200,
                        "purchase": 600
                    }
                }, # expected_response
                200 #  expected_response_code
            ),
            (
                "invalid", "1", "2", "valid", "valid", None,
                {"error": "Start date must be earlier than or equal to end date."},
                400
            )
        ],
        indirect=["mock_date_range", "mock_product", "mock_company"]
    )
    @patch('analytics.parse_date_range')
    @patch('analytics.get_entry_totals_filtered')
    @patch('analytics.get_user_item_or_404')
    def test_global_summary(self, mock_get_or_404, mock_entry_totals, mock_parse_date,
                            mock_date_range, mock_product_id, mock_company_id,
                            mock_company, mock_product, mock_entry_totals_data,
                            expected_response, expected_response_code, app):

        # if mock_company:
        #     company_mock = MagicMock(spec_set=Company, **mock_company)
        #     mock_get_or_404.return_value = company_mock
        # else:
        #     mock_get_or_404.side_effect = NotFound(description="Unauthorized or company not found!")
        #
        # if mock_product:
        #     product_mock = MagicMock(spec_set=Product, **mock_product)
        #     mock_get_or_404.return_value = product_mock
        # else:
        #     mock_get_or_404.side_effect = NotFound(description="Unauthorized or product not found!")
        mock_get_or_404.side_effect = get_user_item_or_404_side_effect


        if "start" in mock_date_range:
            mock_parse_date.return_value = (mock_date_range["start"], mock_date_range["end"])
        else:
            mock_parse_date.side_effect = ValueError(mock_date_range["ValueError"])

        mock_entry_totals.return_value = mock_entry_totals_data