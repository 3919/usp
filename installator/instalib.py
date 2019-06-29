import os

def fetchPath(msg, errmsg, verify):
    isOk = False

    arg = input(msg)
    isOk = verify(os.path.expanduser(arg))

    while not isOk:
        print(errmsg)
        arg = input(msg)
        isOk = verify(os.path.expanduser(arg))

    return arg

class CompilationException(Exception):
    pass

