import sys 

def toLocalPathSeparator(path):
    if sys.platform == "linux":
        return path.replace('\\','/')
    return path.replace('/','\\')
