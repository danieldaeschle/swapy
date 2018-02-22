from .. import _utils
from .. import middlewares


def init():
    module = _utils.caller()
    _utils.register_route(module, '/docs', ['GET'])(_route(module))


def _route(module):
    @middlewares.JsonMiddleware
    def handle():
        routes = sorted(list(map(lambda k: {
            'url': _utils.state(module).routes[k]['url'],
            'docs': _utils.state(module).routes[k]['docs'],
            'methods': list(_utils.state(module).routes[k]['methods'])
        }, _utils.state(module).routes.keys())), key=lambda r: r['url'])
        return routes
    return handle
