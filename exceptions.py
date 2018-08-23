from traceback import format_exc


class LambdaUtilsException(Exception):
    def __init__(self, err_msg):
        self.err_msg = err_msg
        self.trace = format_exc()


class NoSuchOriginKey(LambdaUtilsException):
    def __init__(self, err_msg):
        super().__init__(err_msg)


class InternalError(LambdaUtilsException):
    def __init__(self, err_msg):
        super().__init__(err_msg)


class Warming(Exception):
    pass
