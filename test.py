from sapy import on_get, run, include, use, on, error
from sapy.middlewares import JsonMiddleware, JsonException
import another

error(JsonException)
use(JsonMiddleware)
include(another, '/v1')


@on_get()
def root():
    return 'test', 200


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
