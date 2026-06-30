# Maybe useful for integration, e2e

# @pytest.fixture(scope='function')
# def app():
#     """App fixture to register the routes."""
#     app = Flask(__name__)
#     app.testing = True
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # or your test database URL
#     app.config['TESTING'] = True
#
#     with app.app_context():
#         db.create_all()
#
#     yield app
#     # Tear down the database after the test
#     with app.app_context():
#         db.session.remove()  # Remove session
#         db.drop_all()  # Drop all tables
#
#     # Mock view function get product
#     @app.route("/mock-endpoint/<int:product_id>")
#     def mock_get_product(product_id):
#
#         return get_product(product_id)
#
#     return app
#
# @pytest.fixture(scope='function')
# def client(app):
#     """Test client fixture."""
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # or your test database URL
#     app.config['TESTING'] = True
#
#     return app.test_client()




# import pytest
# from unittest.mock import patch, MagicMock
# from models import Product
# from products import get_product
#
# class TestProductModels:
#
#     @patch('products.db.session.add')  # Mock db.session.add for creating a product
#     @patch('products.db.session.commit')  # Mock db.session.commit
#     def test_create_product(self, mock_add, mock_commit, app, client):
#         """Unit test for creating a product without a real DB."""
#
#         response = client.post('/products', json={
#                 "name": "New Product",
#                 "customs_code": "2",
#                 "img_url": "https://newproduct.com",
#         })
#
#         # Additional inspections
#         print(f"\n\n\n\nMock call arguments:{mock_add.call_args}!!!\n\n\n")  # Print latest call
#         print(mock_add.call_count)  # Print number of times called
#
#         mock_add.assert_called_once()  # Ensure db.session.add was called
#         mock_commit.assert_called_once()  # Ensure db.session.commit was called
#         assert response.status_code == 201
#
#     @patch("products.db.get_or_404")
#     def test_get_product(self, mock_get_or_404, client, app):
#         """Unit test for get_product without using a real database."""
#
#         with app.app_context():
#             # Mock the return value for db.get_or_404
#             mock_product = Product(id=1, name="Mock Product", customs_code="1", img_url="https://example.com", user_id=1)
#             mock_get_or_404.return_value = mock_product
#
#             # Call the function directly (not through Flask)
#             # response = get_product(2)
#             response = client.get('/products/1')  # Test the endpoint for product with ID=1
#
#         # Assertions
#         mock_get_or_404.assert_called_once_with(Product, 1)  # Ensure db.get_or_404 was called with the correct arguments
#         assert response.status_code == 200
#         assert response.json == {"product": mock_product.to_dict()}



# SQLALCHEMY_DATABASE_URI='sqlite:///chemical_db.db'