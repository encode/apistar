# from apistar.test import TestClient
from app import welcome


def test_welcome():
    """
    Testing a view directly.
    """
    response = welcome()
    assert response.data == {'message': 'Welcome to API Star!'}

# def test_get_hello(test_client: TestClient):
#     """
#     Testing using the `requests` test client.
#     """
#     response = test_client.get('/')
#     assert response.status_code == 200
#     assert response.json() == {'message': 'Hello, API Star!'}
