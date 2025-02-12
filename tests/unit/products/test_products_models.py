import pytest
import sys
import os
from unittest.mock import patch, MagicMock

from werkzeug.exceptions import NotFound

from products import User, Product

# Add the directory containing 'models.py' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from models import Product, User
from products import get_product, get_products, delete_product

class TestProductModels:

    @pytest.mark.parametrize(
        "mock_product_data, expected_product_count, expected_status_code",
        [
            # Scenario 1: Valid Products
            ([
                 {"id": 1, "name": "Mock Product 1", "customs_code": "1", "img_url": "https://example.com"},
                 {"id": 2, "name": "Mock Product 2", "customs_code": "2", "img_url": "https://example.com"}
             ], 2, 200),

            # Scenario 2: Empty Products
            ([], 0, 200)
        ]
    )
    @patch("products.User.query")
    @patch("products.Product.query")
    def test_get_products(self,mock_product_query, mock_user_query, mock_product_data, expected_product_count, expected_status_code, app):
        """Unit test for get_product without using a real database."""

        # Prepare the mock products list
        mock_products = []
        for product_data in mock_product_data:
            mock_product = MagicMock(spec=Product, **product_data)
            mock_product.to_dict.return_value = product_data
            mock_products.append(mock_product)

        # Mock the database queries
        mock_product_query.all.return_value = mock_products
        mock_user_query.get.return_value = MagicMock(spec=User)

        # Call the function directly (not through Flask)
        with app.app_context():
            with app.test_request_context():
                # result = client.get("/products")
                result = get_products()

        response_data = result[0].json
        status_code = result[1]

        # Assertions
        mock_product_query.all.assert_called_once()  # Ensure Product.query.all was called
        mock_user_query.get.assert_called_once_with(1)  # Ensure User.query.get was called with 1

        # Check the returned status code
        assert status_code == expected_status_code  # Status code should be 200
        # Check if the returned data matches the expected product count
        assert len(response_data) == expected_product_count
        # Check the details of the products in the response (if there are any)
        if expected_product_count > 0:
            assert response_data[0]['name'] == "Mock Product 1"  # Check the first product name
            assert response_data[1]['name'] == "Mock Product 2"  # Check the second product name
            assert "id" in response_data[0]  # Ensure the 'id' key exists
            assert "customs_code" in response_data[0]  # Ensure the 'customs_code' key exists
        else:
            # If there are no products, ensure the response data is an empty list
            assert response_data == []

    @pytest.mark.parametrize(
        "mock_product_data, response_keyword, status_code",
        [
            # Scenario 1: Valid Product
            ({"id": 1, "name": "Mock Product", "customs_code": "1", "img_url": "https://example.com"}, "product", 200),
            # Scenario 2: Invalid Product
            (None, "error", 404)
        ])
    @patch('products.db.get_or_404')  # Mock Product.query.get_or_404 for fetching a product by ID
    def test_gets_product(self, mock_get_or_404, mock_product_data, response_keyword, status_code, app):
        """Unit test for retrieving a single product by ID without using a real database."""
        # Mock a single product
        if mock_product_data is not None:
            mock_product = MagicMock(spec=Product, **mock_product_data)
            mock_product.to_dict.return_value = mock_product_data
            mock_get_or_404.return_value = mock_product
        else:
            mock_get_or_404.side_effect = NotFound()
        # mock_product = Product(id=1, name="Mock Product", customs_code="1", img_url="https://example.com", user_id=1)
        with app.app_context():
            with app.test_request_context():
                # Call the function directly (not through Flask)
                result = get_product(1)  # Fetch product with ID 1

        # Extract the response data (the JSON payload)
        response_data = result[0].json  # The response is a tuple (Response, status_code)
        print(f"{response_data}: RESPONSE DATA")


        print(f"MOCK FUNC COUNT:{mock_get_or_404.call_count}, CALL ARGS: {mock_get_or_404.call_args}, {mock_get_or_404.method_calls}.")
        # Assertions
        mock_get_or_404.assert_called_once_with(Product, 1)  # Ensure get_or_404 was called with Product and ID 1
        assert isinstance(response_data, dict)  # We expect the result to be a dictionary
        if mock_product_data is not None:
            assert response_keyword in response_data # Ensure there is a product keyword in response
            assert response_data['product']['name'] == "Mock Product"  # Ensure the correct product name is returned
            assert response_data['product']['id'] == 1  # Ensure the correct product ID is returned
            assert response_data['product']['customs_code'] == "1"  # Ensure the correct customs_code is returned
            assert response_data['product']['img_url'] == "https://example.com"  # Ensure the correct image URL is returned
        else:
            assert response_keyword in response_data # Ensure there is an error keyword in the response
            assert response_data['error'] == f"Product of ID: 1 not found."

    @pytest.mark.parametrize(
        "mock_product_data, response_keyword, status_code",
        [
            # Scenario 1: Valid Product
            ({"id": 1, "name": "Mock Product", "customs_code": "1", "img_url": "https://example.com"}, "product", 200),
            # Scenario 2: Invalid Product
            (None, "error", 404)
        ])
    @patch('products.db.get_or_404')  # Mock db.get_or_404 for fetching a product by ID
    @patch('products.db.session.delete')  # Mock db.session.delete for deleting a product
    @patch('products.db.session.commit')  # Mock db.session.commit
    def test_delete_product(self, mock_commit, mock_delete, mock_get_or_404,mock_product_data, response_keyword, status_code, app):
        """Unit test for creating a product without a real DB."""
        if mock_product_data is not None:
            mock_product = MagicMock(spec=Product, **mock_product_data)
            mock_product.to_dict.return_value = mock_product_data
            mock_get_or_404.return_value = mock_product
        else:
            mock_get_or_404.side_effect = NotFound()

        with app.app_context():
            with app.test_request_context():
                result = delete_product(1)

        response_data = result[0].json
        status_code = result[1]
        print(f"{response_data}: RESPONSE DATA")


        print(f"MOCK FUNC COUNT:{mock_get_or_404.call_count}, CALL ARGS: {mock_get_or_404.call_args}, {mock_get_or_404.method_calls}.")

        # Assertions
        if status_code == 200:
            mock_get_or_404.assert_called_once_with(Product, 1) # Ensure db.get_or_404 was called with the correct arguments
            mock_delete.assert_called_once() # Ensure db.session.delete was called
            mock_commit.assert_called_once() # Ensure db.session.commit was called
            assert "success" in response_data
        else:
            assert response_keyword in response_data
            assert response_data[response_keyword] == "Product of ID: 1 not found."
            assert status_code == 404


