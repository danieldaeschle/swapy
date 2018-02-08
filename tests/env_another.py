import os
import sys

# Only for testing
if os.path.exists('../swapy/__init__.py'):
    sys.path.append(os.path.abspath('../'))
else:
    sys.path.append(os.path.abspath('./'))

import swapy


@swapy.on('env')
def env():
    return swapy.get_env('secret_key')
