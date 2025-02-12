import pytest

@pytest.mark.parametrize(
    "data, expected_result",
    [
        ({"name": "Entry1", "value": 10}, "Entry created successfully"), #Good data
        ({"name": "", "value": 10}, "Name cannot be empty"),  # Bad data
        ({"name": "Entry2", "value": -1}, "Value must be positive"),  # Bad data
    ]
)
def test_create_entry(client, data, expected_result):
    response = client.add_entry(data)
    assert response.message == expected_result