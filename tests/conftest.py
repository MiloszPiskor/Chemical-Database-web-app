import pytest
from flask import Flask, jsonify
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

@pytest.fixture
def app():

    app = Flask(__name__)
    app.config["TESTING"] = True
    with app.app_context():  # <--- Ensures that an application context is created
        yield app

@pytest.fixture
def client(app):

    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()


















#     @app.route("/test_json", methods=["POST"])
#     @validate_json_payload
#     def test_json(data):
#         return jsonify(success=True, data=data), 200
#
#     @app.route("/test_document_nr", methods=["POST"])
#     @validate_json_payload
#     @validate_document_nr
#     def test_document_nr(data):
#         return jsonify(success=True, data=data), 200
#
#     @app.route("/test_transaction", methods=["POST"])
#     @validate_json_payload
#     @validate_transaction_type
#     def test_transaction(data):
#         return jsonify(success=True, data=data), 200
#
#     return app
#
# @pytest.fixture
# def client(app):
#     """Creates a test client."""
#     return app.test_client()
#
# # ---- Test Cases ----
#
# def test_missing_json_payload(client):
#     """Test that missing JSON results in a 400 error."""
#     response = client.post("/test_json", json={})
#     assert response.status_code == 400
#     assert "No JSON data found" in response.json["error"]
#
# def test_invalid_fields(client):
#     """Test invalid fields rejection."""
#     invalid_data = {"invalid_field": "value"}
#     response = client.post("/test_json", json=invalid_data)
#     assert response.status_code == 400
#     assert "Invalid field(s)" in response.json["error"]
#
# def test_valid_document_nr(client):
#     """Test valid WZ document number."""
#     valid_data = {"document_nr": "WZ 123/02/2025"}
#     response = client.post("/test_document_nr", json=valid_data)
#     assert response.status_code == 200
#
# def test_invalid_document_nr(client):
#     """Test invalid WZ document number format."""
#     invalid_data = {"document_nr": "ABC 123"}
#     response = client.post("/test_document_nr", json=invalid_data)
#     assert response.status_code == 400
#     assert "Invalid document number format" in response.json["error"]
#
# def test_invalid_transaction_type(client):
#     """Test invalid transaction type."""
#     invalid_data = {"transaction_type": "InvalidType"}
#     response = client.post("/test_transaction", json=invalid_data)
#     assert response.status_code == 400
#     assert "Invalid data in the 'transaction type'" in response.json["error"]