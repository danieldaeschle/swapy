import os
import sys

# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))

import swapy
import env_another

swapy.include(env_another)

swapy.environment({
    'production': {
        'secret_key': 'secret'
    },
    'development': {
        'secret_key': 'not_secret'
    }
})


@swapy.on_get('checkSecretKey')
def env():
    return swapy. get_env('secret_key')


@swapy.on_get('set_secure_cookie')
def secure_cookie(req):
    req.secure_cookie['key'] = 'value'


@swapy.on_get('get_secure_cookie')
def secure_cookie(req):
    return req.secure_cookie.get('key')


application = swapy.app()
