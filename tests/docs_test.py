import sys
import os
# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))
import swapy
from swapy.ext import api_docs
from swapy.testing import client

api_docs.init()


@swapy.on('test')
def test():
    return 'Hi!'


c = client(swapy.app())


if __name__ == '__main__':
    swapy.run(debug=True)


# def test_works():
#     r = c.get('docs')
#     assert r.data.decode() == 'Docs!'
