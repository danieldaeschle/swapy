import sys
import os
sys.path.append(os.path.abspath('../'))

from swapy import on


@on('/test')
def test():
    return 'Hello, I\'m Test!'
