class LambdaError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TransientError(LambdaError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PermanentError(LambdaError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ExceedMaximumRetry(TransientError):
    def __init__(self, err_msg, **kwargs):
        super().__init__(err_msg, **kwargs)


class InternalError(TransientError):
    def __init__(self, err_msg, **kwargs):
        super().__init__(err_msg, **kwargs)


class UnexpectedError(PermanentError):
    def __init__(self, err_msg, **kwargs):
        super().__init__(err_msg, **kwargs)
