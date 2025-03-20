from unittest.mock import MagicMock, patch
from models import Product, Company
from utils import update_product_stock, validate_product_data, product_check, validate_company_data, single_line_item_validation
import pytest

class TestUtilFunctions:

    @pytest.mark.parametrize(
        "initial_stock, mock_transaction_type, mock_quantity, expected_error, expected_stock",
    [
        (0, "Supply", 48, None, 48), # Scenario 1 - Supply case
        (11, "Purchase", 12, ValueError, -1), # Scenario 2 - Purchase case: insufficient stock
        (12, "Purchase", 12, None, 0) # Scenario 3 - Purchase case: sufficient stock
    ],
    )
    def test_update_product_stock(self, initial_stock, mock_transaction_type, mock_quantity, expected_error, expected_stock, app):
        """Tests the update_product_stock function for different transaction scenarios."""

        mock_product = MagicMock(spec = Product)
        mock_product.stock = initial_stock

        if expected_error:
            with pytest.raises(expected_error):
                with app.app_context():
                    with app.test_request_context():
                        update_product_stock(mock_product, mock_transaction_type, mock_quantity)
                        assert mock_product.stock == initial_stock # Stock remains unchanged on failure

        else:
            with app.app_context():
                with app.test_request_context():
                    update_product_stock(mock_product, mock_transaction_type, mock_quantity)
                    assert mock_product.stock == expected_stock # Stock updates correctly

    @pytest.mark.parametrize(
        "data, mock_product_check_return, expected_return, is_update",
        [
            # Scenario 1: Successful validation
            ({ "name": "Big Orange", "customs_code": "22375", "img_url": "https://example.com"}, None, None, False),
            # Scenario 2: Unsuccessful validation: invalid field
            ({ "name": "Big Orange", "customs_code": "22375", "img_url": "https://example.com", "invalid" : "extra"},
             None, "Invalid field(s): invalid.", False),
            # Scenario 3: Unsuccessful validation: missing required field
            ({ "name": "Big Orange", "img_url": "https://example.com"}, None, "The following fields cannot be empty: customs_code.", False),
            # Scenario 4: Unsuccessful validation: name already exists
            ({ "name": "Zep 45", "customs_code": "22375", "img_url": "https://example.com"}, "A product of this name already exists.", "A product of this name already exists.", True)
        ]
    )
    @patch('utils.product_check')
    def test_validate_product_data(self, mock_product_check, data, mock_product_check_return, expected_return, is_update, app):
        """Tests the validate_product_data function with different inputs."""

        # Mock product instance
        mock_product = MagicMock(spec = Product)

        # Mock product_check return value
        mock_product_check.return_value = mock_product_check_return

        # Call function and check return value
        assert validate_product_data(data, mock_product if is_update else None, is_update) == expected_return

    @pytest.mark.parametrize(
        "data, mock_company_check_return, expected_return, is_update",
        [
            # Scenario 1: Successful validation
            ({"name": "Talk O' Clock", "address": "Wałbrzych ul. Kolonialna", "contact_person": "Kaja Maja",
              "contact_number": "+48123456789"}, None, None, False),
            # Scenario 2: Invalid field present
            ({"name": "Talk O' Clock", "address": "Wałbrzych ul. Kolonialna", "contact_person": "Kaja Maja",
              "contact_number": "+48123456789", "invalid_field": "extra"},
             None, "Invalid field(s): invalid_field.", False),
            # Scenario 3: Missing required field
            ({"name": "Talk O' Clock", "address": "Wałbrzych ul. Kolonialna", "contact_person": "Kaja Maja"}, None,
             "The following fields cannot be empty: contact_number.", False),
            # Scenario 4: Name already exists
            ({"name": "Global Ltd", "address": "London, UK", "contact_person": "John Doe",
              "contact_number": "+447911223344"}, "This name is already occupied by another Company.",
             "This name is already occupied by another Company.", True)
        ]
    )
    @patch('utils.company_check')
    def test_validate_company_data(self, mock_company_check, data, mock_company_check_return, expected_return, is_update,
                                   app):
        """Tests the validate_company_data function with various input scenarios."""

        # Mock company instance
        mock_company = MagicMock(spec = Company)
        mock_company.name = "Existing Company"

        mock_company_check.return_value = mock_company_check_return  # Mock company_check return value

        # Call function and assert the expected return value
        assert validate_company_data(data, mock_company if is_update else None, is_update) == expected_return

    @pytest.mark.parametrize(
        "data, expected_return, product_found",
        [
            # Scenario 1: Successful validation
            ([{"quantity" : 121, "price_per_unit" : 13, "product" : "Zep 45"},
              {"quantity" : 48, "price_per_unit" : 13, "product" : "Big Orange"}], None, True),
            # Scenario 2: Invalid Data (empty list)
            ([], "Empty list or incorrect data format for line items.", False),
            # Scenario 3: Invalid Data (incorrect format)
            (({"quantity" : 121, "price_per_unit" : 13, "product" : "Zep 45"},
              {"quantity" : 48, "price_per_unit" : 13, "product" : "Big Orange"}), "Empty list or incorrect data format for line items.", True),
            # Scenario 4: Invalid Data (Product not found in the database)
            ([{"quantity" : 121, "price_per_unit" : 13, "product" : "Zep 45"},
              {"quantity" : 48, "price_per_unit" : 13, "product" : "Big Orange"}],
             "No such product: Zep 45 found in the database while trying to create new Entry.", False)
        ])
    @patch('utils.Product.query')
    def test_single_line_item_validation(self, mock_query, data, expected_return, product_found, app):
        """Test of utility function single_line_item_validation."""
        mock_product = MagicMock(spec = Product) if product_found else None
        mock_query.filter_by.return_value.first.return_value = mock_product  # Simulate that a product was or wasn't found

        with app.app_context():
            with app.test_request_context():
                result = single_line_item_validation(data)

        # Assert for error cases
        if expected_return:
            assert result[0].get_json()['error'] == expected_return
            assert result[1] == 400

        else:
            # Assert: In the case of a successful validation (no error)
            # Ensure that the products were queried correctly for each line item
            for line_item in data:
                product_name = line_item.get('product')
                mock_query.filter_by.assert_any_call(name=product_name)
                # If there's no return value, we assume success, so we can verify that line items were validated correctly
                assert len(result) == len(data)  # Validate that the line items are returned as expected

    def test_get_or_create_product_company(self):

        pass








