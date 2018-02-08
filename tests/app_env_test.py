import os
import sys

# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))

from swapy.testing import client
from app_env import application

c = client(application)


def test_environment():
    r = c.get('checkSecretKey')
    assert r.data == b'secret'


def test_env_another():
    r = c.get('env')
    assert r.data == b'secret'


def test_secure_cookie():
    c.get('set_secure_cookie')
    r = c.get('get_secure_cookie')
    assert r.data == b'value'
