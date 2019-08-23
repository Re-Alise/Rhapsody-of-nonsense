


def debug(fun):

    def _fun(*args, **kw):
        print('{:^50}'.format(fun.__name__).replace(' ', '-'))
        fun(*args, **kw)
        print('-----'*10)

    return _fun

@debug
def test(x):
    print(x)

test(1)