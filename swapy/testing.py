from werkzeug.wrappers import Response as _Response
from werkzeug.test import Client as _Client


def client(app):
    """
    Returns the werkzeug Client class with the Response class

    :param app: function
        The application function
    :return: Client
    """
    return _Client(app, _Response)
