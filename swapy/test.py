from werkzeug.wrappers import Response
from werkzeug.test import Client


def client(app):
    return Client(app, Response)
