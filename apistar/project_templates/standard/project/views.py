from apistar import Response


def welcome() -> Response:
    return Response({'message': 'Welcome to API Star!'})
