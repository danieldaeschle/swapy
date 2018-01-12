import json

class Request(object):
    def __init__(self, method, headers={}, body='', cookies={}, ip='', params={}, files={}, form={}, url=''):
        self.body = body
        self.url = url
        self.cookies = cookies
        self.ip = ip
        self.params = params
        self.files = files
        self.form = form
        self.headers = headers
        self.method = method

    @property
    def json(self):
        res = {}
        try:
            json.loads(self.body)
        except Exception:
            pass
        return res
