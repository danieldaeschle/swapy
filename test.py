from sapy import on_get, run, include, use, on_error
from sapy.decorators import json
from sapy.error import json_catch
import another

use(json)
on_error(json_catch)
include(another)

@on_get()
def root():
    return 'asd'

if __name__ == '__main__':
    run()
