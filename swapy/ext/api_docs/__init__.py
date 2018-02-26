# noinspection PyProtectedMember
from swapy import _utils
import swapy
from swapy.middlewares import HtmlMiddleware
import os


def init():
    module = _utils.caller()
    module_frame = _utils.caller_frame()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    _utils.shared(module_frame, os.path.join(base_dir, 'static'), '/docs-static')
    _utils.register_route(module, '/docs', ['GET'])(_route(module))


def _route(module):
    @HtmlMiddleware
    def handle():
        routes = sorted(filter(lambda i: i['url'] != '/docs' and i['url'] != '/docs-style', list(map(lambda k: {
            'url': _utils.state(module).routes[k]['url'],
            'docs': _utils.state(module).routes[k]['docs'],
            'methods': list(_utils.state(module).routes[k]['methods'])
        }, _utils.state(module).routes.keys()))), key=lambda r: r['url'])
        return swapy.render('api_docs.html', routes=routes)
    return handle
