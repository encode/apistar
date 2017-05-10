def welcome(username: str=None):
    if username is None:
        message = 'Welcome to API Star!'
    else:
        message = 'Welcome to API Star, %s!' % username

    return {'message': message}
