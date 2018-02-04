from werkzeug.wrappers import Request as WRequest
import json


def response_from(args):
    """
    Casts a result from a route function into a response object

    :param args: object
    :return: Response
    """
    if isinstance(args, tuple):
        if len(args) == 1 and isinstance(args[0], Response):
            return args[0]
        return Response(*args)
    elif isinstance(args, Response):
        return args
    else:
        return Response(args)


class Request(WRequest):
    """
    Request class which inherits from werkzeug's request class
    It adds the json function
    """
    session = None

    @property
    def json(self):
        """
        Returns dict from json string if available

        :return: dict
        """
        try:
            content = json.loads(self.data.decode())
        except json.JSONDecodeError:
            content = {}
        return content


class Response:
    __slots__ = ['content', 'code', 'headers', '_cookies']

    def __init__(self, content=None, code=200, headers=None):
        if headers is None:
            headers = {}
        if content is None:
            content = ''
        self.content = content
        self.code = code
        self.headers = headers
        self._cookies = {}

    def cookies(self, data):
        for key in data.keys():
            self._cookies[key] = data[key]

    def get_cookies(self):
        return self._cookies
