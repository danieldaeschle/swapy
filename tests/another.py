import sys
import os
# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))
from swapy import on


@on('/test')
def test():
    return 'Hello, I\'m Test!'
