class TestEngine:
    def __init__(self):
        self.triesCount = 0
        self.successCount = 0
        self.failsCount = 0
        self.failedTests = []
        self.failedTestsException = []

    def runTest(self, test, arg=None):
        self.triesCount += 1
        ret = False
        try:
            if arg == None:
                ret = test()
            else:
                ret = test(arg)
        except Exception as e:
            self.failedTestsException.append(e)

        if ret: 
            self.successCount += 1
        else:
            self.failsCount += 1
            self.failedTests.append(test.__name__)

    def getStatus(self):
        symbols = [sym for sym in dir(self) if not sym.startswith('__') and not callable(self.__getattribute__(sym))]
        attrs = {}
        for symbol in symbols:
            attrs[symbol.__str__()] = self.__getattribute__(symbol.__str__())

        return attrs


if __name__ == '__main__':
    exit()
