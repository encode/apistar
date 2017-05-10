def welcome(username=None):
    if username is None:
        message = 'Welcome to API Star!'
    else:
        message = f'Welcome to API Star, {username}!'

    return {'message': message}
