def fetchArg(msg, errmsg, verify):
    isOk = False

    arg = input(msg)
    isOk = verify(arg)

    while not isOk:
        print(errmsg)
        arg = input(msg)
        isOk = verify(arg)
    
    return arg

class CompilationException(Exception):
    pass

