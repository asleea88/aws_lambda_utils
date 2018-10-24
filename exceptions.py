from traceback import format_exc


class LambdaUtilsException(Exception):
    def __init__(self, err_msg, **kwargs):
        self.err_msg = err_msg
        self.kwargs = kwargs
        self.trace = format_exc()


class NoSuchOriginKey(LambdaUtilsException):
    def __init__(self, err_msg, **kwargs):
        super().__init__(err_msg, **kwargs)


class ExceedMaximumRetry(LambdaUtilsException):
    def __init__(self, err_msg, **kwargs):
        super().__init__(err_msg, **kwargs)


class UnexpectedError(LambdaUtilsException):
    def __init__(self, err_msg, **kwargs):
        super().__init__(err_msg, **kwargs)


class InternalError(LambdaUtilsException):
    """
    err_msg
        - 0-SizeObject
        - NoRecord
    """
    def __init__(self, err_msg, **kwargs):
        super().__init__(err_msg, **kwargs)


class Warming(Exception):
    pass
