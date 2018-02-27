# noinspection PyProtectedMember
from swapy import _utils
import swapy
from swapy.middlewares import HtmlMiddleware
import os


def init(path='/docs'):
    """
    Initializes this extension to a swapy module

    It registers following routes:
    - /docs (default)
    - /docs-static (default) (for resources like styles)

    :param path: str
        URL endpoint path for which will be routed
        Default: '/docs'
    """
    if not path.startswith('/'):
        path = '/' + path
    module = _utils.caller()
    module_frame = _utils.caller_frame()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    _utils.shared(module_frame, os.path.join(base_dir, 'static'), path + '-static')
    _utils.register_route(module, path, ['GET'])(_route(module))


def _route(module):
    """
    Adding route handler

    :param module: str
        Name of the target module
    """
    @HtmlMiddleware
    def handle():
        routes = sorted(filter(lambda i: i['url'] != '/docs' and i['url'] != '/docs-style', list(map(lambda k: {
            'url': _utils.state(module).routes[k]['url'],
            'docs': _utils.state(module).routes[k]['docs'],
            'methods': list(_utils.state(module).routes[k]['methods'])
        }, _utils.state(module).routes.keys()))), key=lambda r: r['url'])
        return swapy.render('api_docs.html', routes=routes)
    return handle
