from sapy import on


@on('/test')
def test():
    return 'Hello, I\'m Test!'
