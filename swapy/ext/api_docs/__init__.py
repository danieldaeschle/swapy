from jinja2 import DictLoader
from jinja2.environment import Environment
import os
# noinspection PyProtectedMember
from swapy import _utils
import swapy
from swapy.middlewares import HtmlMiddleware


def init():
    module = _utils.caller()
    _utils.register_route(module, '/docs', ['GET'])(_route(module))
    _utils.register_route(module, '/docs-style', ['GET'])(_style)


def _render(args):
    loc = os.path.dirname(os.path.abspath(__file__))
    pages = ('api_docs.html', 'bulma.css')
    templates = dict((name, open('{}\\{}'.format(loc, name), 'r').read()) for name in pages)
    env = Environment()
    env.loader = DictLoader(templates)
    template = env.get_template('api_docs.html')
    return template.render(routes=args)


def _style():
    return swapy.file('bulma.css')


def _route(module):
    @HtmlMiddleware
    def handle():
        routes = sorted(filter(lambda i: i['url'] != '/docs' and i['url'] != '/docs-style', list(map(lambda k: {
            'url': _utils.state(module).routes[k]['url'],
            'docs': _utils.state(module).routes[k]['docs'],
            'methods': list(_utils.state(module).routes[k]['methods'])
        }, _utils.state(module).routes.keys()))), key=lambda r: r['url'])
        return _render(routes)
    return handle
