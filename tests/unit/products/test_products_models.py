import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import logging
from flask import has_request_context, request

from werkzeug.exceptions import NotFound

# Add the directory containing 'models.py' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from models import Product, User
from products import get_product, get_products, delete_product, edit_product, add_product

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
    @patch('products.user.products')
    def test_get_products(self, mock_user_products, mock_user_query, mock_product_data, expected_product_count, expected_status_code, app):
        """Unit test for get_product without using a real database."""

        # Prepare the mock products list
        mock_products = []
        for product_data in mock_product_data:
            mock_product = MagicMock(spec=Product, **product_data)
            mock_product.to_dict.return_value = product_data
            mock_products.append(mock_product)

        # Mock the database queries
        mock_user_products.return_value = mock_products
        mock_user_query.get.return_value = MagicMock(spec=User)

        # Call the function directly (not through Flask)
        with app.app_context():
            with app.test_request_context():
                # result = client.get("/products")
                result = get_products()

        response_data = result[0].json
        status_code = result[1]

        # Assertions
        mock_user_products.assert_called_once()  # Ensure Product.query.all was called
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
            mock_product = MagicMock(spec=Product)
            # Set attributes dynamically
            for key, value in mock_product_data.items():
                setattr(mock_product, key, value)

            mock_get_or_404.return_value = mock_product

            # Ensure to_dict() returns a real dictionary
            mock_product.to_dict.return_value = mock_product_data

        else:
            mock_get_or_404.side_effect = NotFound()
        # mock_product = Product(id=1, name="Mock Product", customs_code="1", img_url="https://example.com", user_id=1)
        with app.app_context():
            with app.test_request_context():
                # Call the function directly (not through Flask)
                result = get_product(1)  # Fetch product with ID 1

        # Extract the response data (the JSON payload)
        response_data = result[0].json  # The response is a tuple (Response, status_code)
        print(f" here {response_data}: RESPONSE DATA")


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

            # Dynamically mock the to_dict() method to return a dictionary based on the object's attributes
            def dynamic_to_dict():
                return {key: getattr(mock_product, key) for key in mock_product.__dict__ if not key.startswith('_')}

            mock_product.to_dict.side_effect = dynamic_to_dict  # Set to use dynamic_to_dict function

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

    @pytest.mark.parametrize(
        "mock_product_data, mock_request_data, validation_return, expected_status_code, expected_response",
        [
            # Scenario 1: Valid Product Update
            ({"customs_code": "12345", "id": 1, "img_url": "https://www.example.com", "name": "Mock Product",
              "stock": 0.0, "user_id": 1},
             {"customs_code": "1234", "img_url": "https://www.example.com", "name": "Mock Product"}, None, 200,
             {"customs_code": "1234", "name": "Mock Product", "img_url": "https://www.example.com"}),

            # Scenario 2: Invalid Product Update (missing field)
            ({"customs_code": "12345", "id": 1, "img_url": "https://www.example.com", "name": "Mock Product",
             "stock": 0.0, "user_id": 1},
            {"img_url": "https://www.example.com", "name": "Mock Product"}, "The following fields cannot be empty: customs_code.", 400,
            {"error": "The following fields cannot be empty: customs_code."}),

             #Scenario 3: Invalid Product Update (name already exists)
            ({"customs_code": "12345", "id": 1, "img_url": "https://www.example.com", "name": "Mock Product",
              "stock": 0.0, "user_id": 1},
             {"customs_code": "12345", "img_url": "https://www.example.com", "name": "Mocked Product"}, "A product of this name already exists.", 400,
             {"error" : "A product of this name already exists."}),

            # Scenario 4: Invalid Product Update (product doesn't exist)
            (None, {"customs_code": "1234", "img_url": "https://www.example.com", "name": "Mock Product"}, None, 404, {"error": "Product of ID: 1 not found."})
        ])
    @patch('products.db.get_or_404')
    @patch('products.db.session.commit')
    @patch('products.validate_product_data')
    def test_edit_product(self, mock_validate_product_data, mock_commit, mock_get_or_404,
                          mock_product_data, mock_request_data, validation_return, expected_status_code, expected_response, app):
        """Unit test for editing a product without a real DB."""

        if mock_product_data is not None:
            # Assert that the product exists
            mock_product = MagicMock(spec=Product, **mock_product_data)

            def dynamic_to_dict():  # Dynamically return a dictionary based on the object's attributes
                return {column: getattr(mock_product, column) for column in mock_product_data.keys()} # Return a dictionary of the object's attributes

            mock_product.to_dict.side_effect = dynamic_to_dict
            mock_get_or_404.return_value = mock_product
        else:
            # Assert that the product doesn't exist
            mock_get_or_404.side_effect = NotFound()

        # Mock the validation function (simulate validation failure or success):::: test of this function is in test_utils.py
        mock_validate_product_data.return_value = validation_return

        with app.app_context():
            with app.test_request_context(json=mock_request_data):
                with patch.object(request, "get_json", return_value=mock_request_data) as mock_get_json:   # Mock the request data
                    logging.debug(f"Request context active inside: {has_request_context()}")

                    result = edit_product(1) # Edit product with ID 1

        print(f"Request context active after: {has_request_context()}")
        response_data = result[0].json # Extract the response data (the JSON payload)
        status_code = result[1]        # Extract the status code
        print(f"Status Code: {status_code}")
        print(f"Response Data: {response_data}")
        print(f"Result: {result}")

        # Assertions
        if expected_status_code == 200:
            mock_get_or_404.assert_called_once_with(Product, 1)  # Ensure db.get_or_404 was called with the correct arguments
            mock_get_json.assert_called_once()
            mock_commit.assert_called_once()
            assert status_code == 200
            assert "name" in response_data # Ensure the name key exists in the response data
            assert response_data["customs_code"] == "1234" # Ensure the customs_code was updated
            assert validation_return is None
        elif expected_status_code == 400:
            mock_get_or_404.assert_called_once_with(Product, 1)
            mock_get_json.assert_called_once() # Ensure request.get_json was called
            mock_commit.assert_not_called() # Ensure db.session.commit was not called
            assert status_code == 400
            assert "error" in response_data # Ensure the error key exists in the response data
            assert response_data["error"] == validation_return  # Error messages for different scenarios
        elif expected_status_code == 404:
            mock_commit.assert_not_called() # Ensure db.session.commit was not called
            assert status_code == 404
            assert response_data == expected_response
            mock_get_json.assert_not_called() # Ensure request.get_json was not called

    @pytest.mark.parametrize(
        "mock_product_data, mock_request_data, validation_return, expected_status_code, expected_response",
        [
            # Scenario 1: Valid Product
            ({"customs_code": "12345", "id": 1, "img_url": "https://www.example.com", "name": "Mock Product",
              "stock": 0.0, "user_id": 1},
             {"customs_code": "1234", "img_url": "https://www.example.com", "name": "Mock Product"}, None, 200,
             {'success' : "Successfully created a new product: Mock Product (ID: 1)!"}),

            # Scenario 2: Invalid Product (missing field(s))
            ({"customs_code": "12345", "id": 1, "img_url": "https://www.example.com", "name": "Mock Product",
             "stock": 0.0, "user_id": 1},
            {"img_url": "https://www.example.com", "name": "Mock Product"}, "The following fields cannot be empty: customs_code.", 400,
            {"error": "The following fields cannot be empty: customs_code."}),

             #Scenario 3: Invalid Product (name already exists)
            ({"customs_code": "12345", "id": 1, "img_url": "https://www.example.com", "name": "Mock Product",
              "stock": 0.0, "user_id": 1},
             {"customs_code": "12345", "img_url": "https://www.example.com", "name": "Mocked Product"}, "A product of this name already exists.", 400,
             {"error" : "A product of this name already exists."}),

            # Scenario 4: Invalid Product (invalid field(s))
            ({"customs_code": "12345", "id": 1, "img_url": "https://www.example.com", "name": "Mock Product",
              "stock": 0.0, "user_id": 1},
             {"img_url": "https://www.example.com", "name": "Mock Product", "customs_code": "12345", "extra_field" : "Extra"},
             "Invalid field(s): extra_field", 400,
             {"error": "Invalid field(s): extra_field"}),
        ])
    @patch('products.db.session.add')
    @patch('products.db.session.commit')
    @patch('products.validate_product_data')
    @patch('products.assign_user_to_product')
    @patch('products.Product')
    def test_add_product(self, mock_new_product, mock_assign_user_to_product, mock_validate_product_data, mock_commit, mock_add, mock_product_data, mock_request_data, validation_return, expected_status_code, expected_response, app):
        """Unit test for creating a product without a real DB."""

        mock_product = MagicMock(spec=Product, **mock_product_data) # Mock the product object
        mock_new_product.result_value = mock_product # Set the return value of new_product to the mock product

        mock_validate_product_data.return_value = validation_return # Mock the validation function
        with app.app_context():
            with app.test_request_context(json=mock_request_data): # Mock the request data
                with patch.object(request, "get_json", return_value=mock_request_data) as mock_get_json:   # Mock the request data
                    logging.debug(f"Request context active inside: {has_request_context()}")

                    # mock_get_json.return_value = mock_request_data

                    result = add_product() # Edit product with ID 1

        response_data = result[0].json
        status_code = result[1]

        # Assertions

        if expected_status_code == 200:
            mock_add.assert_called_once() # Ensure db.session.add was called
            mock_commit.assert_called_once() # Ensure db.session.commit was called
            mock_assign_user_to_product.assert_called_once() # Ensure assign_user_to_product was called
            mock_validate_product_data.assert_called_once() # Ensure validate_product_data was called
            assert status_code == expected_status_code
            assert "success" in response_data
        elif expected_status_code == 400:
            mock_validate_product_data.assert_called_once() # Ensure validate_product_data was called
            mock_add.assert_not_called()
            mock_commit.assert_not_called()
            mock_assign_user_to_product.assert_not_called()
            assert status_code == expected_status_code
            assert "error" in response_data






