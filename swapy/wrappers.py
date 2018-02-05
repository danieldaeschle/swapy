from werkzeug.wrappers import BaseRequest
from werkzeug.contrib.securecookie import SecureCookie as SecureCookie
import json
from swapy import _utils


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


class Request(BaseRequest):
    """
    Request class which inherits from werkzeug's request class
    It adds the json function
    """
    session = None
    _secure_cookie = None

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

    @property
    def secure_cookie(self):
        return self.get_secure_cookie(_utils.caller())

    def get_secure_cookie(self, module=None):
        if module is None:
            module = _utils.caller()
        state = _utils.state(module)
        secret_key = state.environment.get('secret_key')
        if not secret_key:
            raise Exception('\'secret_key\' value must be set in environment')
        if not self._secure_cookie:
            self._secure_cookie = SecureCookie.load_cookie(self, secret_key=secret_key.encode())
        return self._secure_cookie


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

    @property
    def cookies(self):
        return self.get_cookies()

    @cookies.setter
    def cookies(self, data):
        self.set_cookies(data)

    def set_cookies(self, data):
        for key in data.keys():
            self._cookies[key] = data[key]

    def get_cookies(self):
        return self._cookies
