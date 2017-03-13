from project.views import welcome


def test_welcome():
    response = welcome()
    assert response.data == {'message': 'Welcome to API Star!'}
