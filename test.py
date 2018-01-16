from sapy import on_get, run, include, use, on, error, send_file, redirect
from sapy.middlewares import JsonMiddleware, JsonException, HtmlMiddleware
import another

error(JsonException)
use(HtmlMiddleware)
include(another, '/v1')


@on_get()
def root():
    return 'Hello Sapify! :)'


@on_get('redirect')
def redirect():
    return redirect('https://google.de')


@on_get('/file')
def file():
    return send_file('test.py')


@on_get('/error')
def error():
    return object


@on_get('json')
def json():
    return {'message': 'hi'}


@on('/*')
def not_found(req):
    return {'message': 'Endpoint \'{}\' doesn\'t exists'.format(req.path)}, 404
    

if __name__ == '__main__':
    run(debug=True)
