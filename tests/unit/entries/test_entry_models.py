import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import current_app, jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import NotFound

# Add the directory containing 'models.py' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Mocking the validator decorators:
patch('utils.requires_auth', lambda x: x).start()
patch('validator_funcs.validate_json_payload', lambda x: x).start()
patch('validator_funcs.validate_document_nr', lambda x: x).start()
patch('validator_funcs.validate_transaction_type', lambda x: x).start()
patch('validator_funcs.validate_date_format', lambda x: x).start()
patch('validator_funcs.validate_line_items', lambda x: x).start()

from entries import get_entry, get_entries, add_entry
from EntryService import EntryService
from models import Entry, User, Company, Product, LineItem


# Helper function to mock the g.user
def mock_user():
    return MagicMock(spec=User)

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

        # noinspection PyUnusedFunction
        def dynamic_to_dict(entry, i):
            return {key: getattr(entry, key) for key in mock_entry_data[i].keys()}

        mock_user = MagicMock(spec=User, id=1)

        if isinstance(mock_entry_data, list):
            mock_entries = [MagicMock(spec=Entry, **entry_data) for entry_data in mock_entry_data] # Prepare the mock entries list

            # Loop through mock_entries and mock_entry_data correctly
            for i, entry_data in enumerate(mock_entry_data):
                mock_entries[i].to_dict.side_effect = lambda entry=mock_entries[i], idx=i: dynamic_to_dict(entry, idx) # Using lambda to prevent the late binding issue, capturing right variables at the right time

            mock_user.entries = mock_entries

        # Simulating a Server Error by raising an Exception
        else:
            def raise_db_error():
                raise Exception("Database connection failed")
            print("Lack of list detected, proceeding to stimulate 500 error...")
            mock_user.entries = MagicMock(side_effect=raise_db_error)
            print(f"The error??? :{mock_user.entries.name}")
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

    # Now testing the chain of 3 functions inside EntryService.py that make up the 'add_entry(*args, **kwargs)' function,
    # testing each one separately since these are unit tests:

    @pytest.mark.parametrize(
        "data, expected_status_code, mock_document_nr_return, mock_company_return, mock_line_items_return, expected_error_message",
        [
            # Scenario 1: Document number already exists
            (
                    {"document_nr": "12345", "company": "Test Company", "line_items": []},
                    400,  # Expected status code
                    True,  # Document exists
                    None,  # Company doesn't matter for this case
                    None,  # No need to validate line items in this case
                    "The entry tied to a transaction: 12345 already exists."
            ),
            # Scenario 2: Company not found
            (
                    {"document_nr": "67890", "company": "Nonexistent Company", "line_items": []},
                    400,  # Expected status code
                    None,  # Document doesn't exist
                    None,  # Company not found
                    None,  # No need to validate line items
                    "Company: Nonexistent Company not found in the database."
            ),
            # Scenario 3: Line item validation failure
            (
                    {"document_nr": "67890", "company": "Test Company", "line_items": ["invalid_item"]},
                    400,  # Expected status code
                    None,  # Document doesn't exist
                    True,  # Company found
                    "No such product: invalid_item found in the database while trying to create new Entry",  # Validation failed
                    "No such product: invalid_item found in the database while trying to create new Entry"
            ),
            # Scenario 4: Successful validation and entry creation
            (
                    {"document_nr": "67890", "company": "Test Company", "line_items": ["item1", "item2"]},
                    200,  # Expected status code
                    None,  # Document doesn't exist
                    True,  # Company found
                    ["item1", "item2"],  # Line item validation successful
                    None  # No error
            ),
            # Scenario 5: Database error
            (
                    {"document_nr": "67890", "company": "Test Company", "line_items": ["item1"]},
                    500,  # Expected status code
                    None,  # Document doesn't exist
                    True,  # Company found
                    ["item1"],  # Line item validation successful
                    "An internal database error occurred. Please try again later."
            ),
        ]
    )
    @patch('EntryService.Entry.query')
    @patch('EntryService.Company.query')
    @patch('EntryService.single_line_item_validation')
    @patch('EntryService.EntryService.save_entry')
    def test_pre_entry_validation(self, mock_save_entry,mock_line_item_validation, mock_company_query, mock_db_query, data,
                                  expected_status_code,
                                  mock_document_nr_return, mock_company_return, mock_line_items_return,
                                  expected_error_message, app):

        def fake_line_item_validation(*args, **kwargs):
            if isinstance(mock_line_items_return, list):
                return mock_line_items_return
            else:
                return (jsonify(error=mock_line_items_return), 400)

        user = mock_user()
        # For Entry
        mock_db_query.filter_by.return_value.first.return_value = (
            MagicMock() if mock_document_nr_return else None
        )

        # For Company
        mock_company_query.filter_by.return_value.first.return_value = (
            MagicMock() if mock_company_return else None
        )

        # For helper validating Line Items
        mock_line_item_validation.side_effect = fake_line_item_validation

        # For stimulating 500 Error
        if expected_status_code == 500:
            from sqlalchemy.exc import SQLAlchemyError
            mock_save_entry.side_effect = SQLAlchemyError("An internal database error occurred. Please try again later.")

        with app.app_context():
            with app.test_request_context():
                response = EntryService.pre_entry_validation( data = data, user = user)

        response_data = response[0].json
        status_code = response[1]

        print(f"Data: {response_data}, s_code: {status_code}.")

        # Assertions

        if expected_status_code == 200:
            # IMPORTANT: NO ASSERTION FOR: status_code == expected_status_code, WHY?
            # Because this function's return is another function: 'save_entry'. Therefore, a successful execution of this
            # func does not have any response thus no s_code or message are asserted
            mock_line_item_validation.assert_called_once()

            # Assert that the Entry query was called with the correct document number.
            mock_db_query.filter_by.assert_called_once_with(document_nr=data.get("document_nr"))
            # Assert that the Company query was called with the correct company name.
            mock_company_query.filter_by.assert_called_once_with(name=data.get("company"))

            # Assert that save_entry was called exactly once with the proper parameters.
            mock_save_entry.assert_called_once_with(data, mock_line_items_return,
                                                    mock_company_query.filter_by.return_value.first.return_value,
                                                    user)

        elif status_code == 400:
            assert status_code == expected_status_code
            mock_db_query.filter_by.assert_called_once_with(document_nr=data.get("document_nr"))
            if mock_document_nr_return:  # Document exists case
                mock_company_query.filter_by.assert_not_called()
                mock_line_item_validation.assert_not_called()
            elif mock_company_return is None:  # Company not found
                mock_company_query.filter_by.assert_called_once_with(name=data.get("company"))
                mock_line_item_validation.assert_not_called()
            else:  # Line item validation failure
                mock_company_query.filter_by.assert_called_once_with(name=data.get("company"))
                mock_line_item_validation.assert_called_once()

        elif status_code == 500:
            assert status_code == expected_status_code
            assert expected_error_message == response_data["error"] == expected_error_message

    @pytest.mark.parametrize(
        "data, validated_line_items, company_to_assign, mock_flush_side_effect, mock_commit_side_effect, mock_process_side_effect, expected_status_code, expected_message",
        [
            # Scenario 1: Successful case
            (
                    {"document_nr": "WZ 2/01/2025", "date" : "2024-02-07", "transaction_type" : "Purchase"}, ["item1", "item2"], "TestCompany",
                    None, None, None, 201, "Entry created successfully!"
            ),
            # Scenario 2: Failure at flush()
            (
                    {"document_nr": "WZ 2/01/2025", "date" : "2024-02-07", "transaction_type" : "Purchase"}, ["item3"], "TestCompany",
                    SQLAlchemyError("Flush failed"), None, None, 500, "Failed to save entry."
            ),
            # Scenario 3: Failure at commit()
            (
                    {"document_nr": "WZ 2/01/2025", "date" : "2024-02-07", "transaction_type" : "Purchase"}, ["item4"], "TestCompany",
                    None, SQLAlchemyError("Commit failed"), None, 500, "Failed to save entry."
            ),
            # Scenario 5: Failure in process_line_items()
            (
                    {"document_nr": "WZ 2/01/2025", "date" : "2024-02-07", "transaction_type" : "Purchase"}, ["item5"], "TestCompany",
                    None, None, ValueError("Insufficient stock for product 'item5'. Current stock: 0, required: 1."), 400, "Failed to save entry : Insufficient stock for product 'item5'. Current stock: 0, required: 1."
            ),
            # Scenario 6: General SQLAlchemyError
            (
                    {"document_nr": "WZ 2/01/2025", "date" : "2024-02-07", "transaction_type" : "Purchase"}, ["item6"], "TestCompany",
                    SQLAlchemyError("Unknown error"), SQLAlchemyError("Unknown error"), None, 500,
                    "Failed to save entry."
            ),
        ]
    )
    @patch('EntryService.db.session.rollback')
    @patch('EntryService.EntryService.process_line_items')
    @patch('EntryService.db.session.commit')
    @patch('EntryService.db.session.flush')
    @patch('EntryService.db.session.add')
    @patch('EntryService.Entry')
    def test_save_entry(self, mock_entry, mock_add, mock_flush, mock_commit, mock_process, mock_rollback, data, validated_line_items, company_to_assign, mock_flush_side_effect, mock_commit_side_effect, mock_process_side_effect, expected_status_code, expected_message, app):

        # Create a Fake Entry Instance
        mock_entry_instance = MagicMock(spec=Entry)
        mock_entry_instance.id = 1 # Manually setting the object's ID due to mocking the real DB
        mock_entry.return_value = mock_entry_instance

        user = mock_user()

        # Apply Side Effects (Exceptions) to Mocks
        mock_flush.side_effect = mock_flush_side_effect
        mock_commit.side_effect = mock_commit_side_effect
        mock_process.side_effect = mock_process_side_effect


        with app.app_context():
            with app.test_request_context():

                response = EntryService.save_entry( data = data, validated_line_items= validated_line_items, company_to_assign = company_to_assign,
                                         user = user)

        response_data = response[0].json
        status_code = response[1]

        # Assertions:
        assert status_code == expected_status_code
        actual_message = response_data.get("message") if expected_status_code == 201 else response_data.get("error")
        assert actual_message == expected_message


        if mock_flush_side_effect:
            # Block 1: Simulate an error during the flush operation, causing a rollback.
            # In this scenario, we expect the 'add' and 'flush' methods to be called once, indicating that the entry is added to the session and an attempt is made to synchronize it.
            # However, since there's an issue during flushing, 'commit' should not be called, and 'rollback' is triggered to ensure database consistency.
            # Additionally, 'process' should not be called, as it depends on successful database modifications, which are prevented here due to the error.
            mock_add.assert_called_once()
            mock_flush.assert_called_once()
            mock_commit.assert_not_called()
            mock_rollback.assert_called_once()
            mock_process.assert_not_called()

        elif mock_commit_side_effect:
            # Block 2: Simulate a failure during the commit operation.
            # In this case, 'add' and 'flush' are still triggered, as changes are attempted to be added to the session.
            # However, the 'commit' fails due to an error, so 'commit' is not called.
            # Since the commit fails, the 'rollback' method is triggered to undo any changes made during this transaction.
            # No processing of line items occurs as the entry creation fails before reaching the processing stage.
            mock_add.assert_called_once()
            mock_flush.assert_called_once()
            mock_commit.assert_called_once()
            mock_rollback.assert_called_once()
            mock_process.assert_called_once_with(mock_entry_instance, validated_line_items, company_to_assign)


        elif mock_process_side_effect:
            # Block 3: Simulate a scenario where the process side effect occurs, leading to no database changes.
            # Here 'add' and 'flush' are triggered because the new Entry is attempted to be created before processing Line Items.
            # However,'commit' is not triggered because no new entry is created eventually due to the process failure.
            # The 'rollback' is therefore called to maintain consistency in case of any partial modifications.
            mock_add.assert_called_once()
            mock_flush.assert_called_once()
            mock_commit.assert_not_called()
            mock_rollback.assert_called_once()

    @pytest.mark.parametrize(
        "validated_line_items, expected_status_code, expected_error_message, mock_get_or_create_product_company_side_effect, mock_update_product_stock_side_effect, mock_db_add_side_effect",
        [
            # Scenario 1: Valid execution
            ([{"product": "product1", "quantity": 10, "price_per_unit": 20}], 200, None, None, None, None),
            # Scenario 2: Error while adding line item to the database
            ([{"product": "product1", "quantity": 10, "price_per_unit": 20}], 500,
             "Database error: Error occurred while adding line item to the database. Please check database constraints or connectivity.",
             None, None, RuntimeError(
                "Database error: Error occurred while adding line item to the database. Please check database constraints or connectivity.")),
            # Scenario 3: Error while creating new ProductCompany model
            ([{"product": "product1", "quantity": 10, "price_per_unit": 20}], 500,
             "Database error: Error occurred while creating new ProductCompany model",
             RuntimeError("Database error: Error occurred while creating new ProductCompany model"), None, None),
            # Scenario 4: Insufficient stock for product
            ([{"product": "product1", "quantity": 10, "price_per_unit": 20}], 500,
             "Failed to save entry : Insufficient stock for product 'product1'. Current stock: 0, required: 10.",
             None, ValueError(
                "Failed to save entry : Insufficient stock for product 'product1'. Current stock: 0, required: 10."),
             None),
        ]
    )
    @patch("EntryService.get_or_create_product_company")
    @patch("EntryService.update_product_stock")
    @patch("EntryService.db.session.add")
    @patch('EntryService.calculate_product_company')
    @patch('EntryService.LineItem')
    @patch('EntryService.Product.query')
    def test_process_line_items(self, mock_product, mock_line_item, mock_calculate, mock_db_add, mock_update_product_stock,
                                mock_get_or_create_product_company, validated_line_items, expected_status_code,
                                expected_error_message, mock_get_or_create_product_company_side_effect,
                                mock_update_product_stock_side_effect, mock_db_add_side_effect, app):

        mock_entry = MagicMock(spec=Entry, id=1)  # Mock Entry Object
        mock_company = MagicMock(spec=Company, id=1)  # Mock the Company object

        # Mock the Line Item object
        mock_line_item_instance = MagicMock(spec=LineItem, id=1)
        mock_line_item.return_value = mock_line_item_instance

        # Mock the Product object
        mock_product.filter_by.return_value.first.return_value = MagicMock(spec=Product, id=1, name="product1")

        # Apply side effects from parameterization
        mock_get_or_create_product_company.side_effect = mock_get_or_create_product_company_side_effect
        mock_update_product_stock.side_effect = mock_update_product_stock_side_effect
        mock_db_add.side_effect = mock_db_add_side_effect

        # Run the function within the app context
        with app.app_context():
            with app.test_request_context():
                try:
                    # Simulate calling the process_line_items function
                    response = EntryService.process_line_items(new_entry=mock_entry, validated_line_items=validated_line_items,
                                                    company_to_assign=mock_company)
                except Exception as e:
                    # Check the exception message and status code
                    assert str(e) == expected_error_message
                    assert expected_status_code == 500

        # Assertions for valid scenario
        if expected_status_code == 200:
            mock_db_add.assert_called()
            mock_update_product_stock.assert_called()
            mock_get_or_create_product_company.assert_called()
            mock_calculate.assert_called()





    # @pytest.mark.parametrize(
    #     "mock_data, company_found, entry_exists, line_item_validation_result, product_stock, transaction_type, expected_status, expected_message",
    #     [
    #         # Scenario 1: Entry already exists (should return 400 with error)
    #         (
    #                 {"document_nr": "123456", "company": "TestCompany",
    #                  "line_items": [{"product": "Product1", "quantity": 5, "price_per_unit": 100}]},
    #                 True,  # Company is found
    #                 True,  # Entry with this document number exists
    #                 [{"product": "Product1", "quantity": 5, "price_per_unit": 100}],  # Valid line items
    #                 100,  # Sufficient stock (irrelevant because entry exists)
    #                 'purchase',  # Transaction type
    #                 400,  # Expected status code
    #                 "The entry tied to a transaction"  # Expected error message
    #         ),
    #         # Scenario 2: Company not found (should return 400 with error)
    #         (
    #                 {"document_nr": "123457", "company": "NonExistingCompany",
    #                  "line_items": [{"product": "Product1", "quantity": 5, "price_per_unit": 100}]},
    #                 False,  # Company is not found
    #                 False,  # Entry with this document number does not exist
    #                 [{"product": "Product1", "quantity": 5, "price_per_unit": 100}],  # Valid line items
    #                 100,  # Sufficient stock (irrelevant because company not found)
    #                 'purchase',  # Transaction type
    #                 400,  # Expected status code
    #                 "Company: NonExistingCompany not found"  # Expected error message
    #         ),
    #         # Scenario 3: Line items validation fails (should return 400 with error)
    #         (
    #                 {"document_nr": "123459", "company": "TestCompany",
    #                  "line_items": [{"product": "InvalidProduct", "quantity": 5, "price_per_unit": 100}]},
    #                 True,  # Company is found
    #                 False,  # Entry with this document number does not exist
    #                 "error",  # Line item validation returns error
    #                 100,  # Sufficient stock (irrelevant because validation fails)
    #                 'purchase',  # Transaction type
    #                 400,  # Expected status code
    #                 "Invalid product or line item."  # Expected error message
    #         ),
    #         # Scenario 4: Insufficient stock for a purchase (should return 400 with error)
    #         (
    #                 {"document_nr": "123460", "company": "TestCompany",
    #                  "line_items": [{"product": "Product1", "quantity": 200, "price_per_unit": 100}]},
    #                 True,  # Company is found
    #                 False,  # Entry with this document number does not exist
    #                 [{"product": "Product1", "quantity": 200, "price_per_unit": 100}],  # Valid line items
    #                 50,  # Insufficient stock
    #                 'purchase',  # Transaction type
    #                 400,  # Expected status code
    #                 "Insufficient stock for product: Product1"  # Expected error message
    #         ),
    #         # Scenario 5: Successful entry creation (should return 201 with success message)
    #         (
    #                 {"document_nr": "123461", "company": "TestCompany",
    #                  "line_items": [{"product": "Product1", "quantity": 5, "price_per_unit": 100}]},
    #                 True,  # Company is found
    #                 False,  # Entry with this document number does not exist
    #                 [{"product": "Product1", "quantity": 5, "price_per_unit": 100}],  # Valid line items
    #                 100,  # Sufficient stock
    #                 'purchase',  # Transaction type
    #                 201,  # Expected status code
    #                 "Entry created successfully!"  # Expected success message
    #         )
    #     ]
    # )
    # @patch('entries.g')  # Mock g to patch g.user
    # @patch('EntryService.Company.query.filter_by')  # Mock Company query
    # @patch('EntryService.Entry.query.filter_by')  # Mock Entry query
    # @patch('utils.single_line_item_validation')  # Mock line item validation
    # @patch('utils.get_or_create_product_company')  # Mock product-company connection creation
    # @patch('utils.calculate_product_company')  # Mock product-company balance calculation
    # @patch('utils.update_product_stock')  # Mock product stock update
    # def test_add_entry(self, mock_update_product_stock, mock_calculate_product_company, mock_get_or_create_product_company,
    #                    mock_line_item_validation, mock_entry_query, mock_company_query, mock_g,
    #                    mock_data, company_found, entry_exists, line_item_validation_result, product_stock,
    #                    transaction_type, expected_status, expected_message, app):
    #     """Test the add_entry function with mock data using parameterization."""
    #
    #     # Mock the user
    #     mock_g.user = mock_user()
    #
    #     # Mocking the company query based on the test case
    #     mock_company = MagicMock(spec=Company, id=1)
    #     mock_company_query.return_value.first.return_value = mock_company if company_found else None
    #
    #     # Mocking Entry query to simulate whether an entry with the document number exists or not
    #     mock_entry_query.return_value.filter_by.return_value.first.return_value = MagicMock() if entry_exists else None
    #
    #     # Mocking line item validation (simulating success or failure)
    #     if line_item_validation_result == "error":
    #         mock_line_item_validation.return_value = (jsonify(error="Invalid product or line item."), 400)
    #     else:
    #         mock_line_item_validation.return_value = line_item_validation_result
    #
    #     # Mocking the product stock check and update behavior
    #     mock_product = MagicMock(spec=Product, id=1)
    #     mock_product.stock = product_stock
    #     mock_get_or_create_product_company.return_value = MagicMock()
    #     mock_calculate_product_company.return_value = None
    #     if transaction_type == 'purchase' and product_stock < sum(item["quantity"] for item in mock_data["line_items"]):
    #         mock_update_product_stock.side_effect = ValueError("Insufficient stock for product: Product1")
    #     else:
    #         mock_update_product_stock.return_value = None
    #
    #     # Simulate a POST request to add an entry
    #     with app.app_context():
    #         with app.test_request_context():
    #             response = add_entry(data=mock_data)
    #
    #     # Assert that the correct status code and message are returned based on the scenario
    #     assert response[1] == expected_status
    #     assert expected_message in response[0].json['error'] if expected_status == 400 else response[0].json['message']
    #
    #     # If the entry creation is successful, check that save_entry was called
    #     if expected_status == 201:
    #         EntryService.save_entry.assert_called_once()
