from traceback import format_exc


class NoSuchOriginKey(Exception):
    def __init__(self, err_msg):
        self.err_msg = err_msg
        self.trace = format_exc()


class InternalError(Exception):
    def __init__(self, err_msg):
        self.err_msg = err_msg
        self.trace = format_exc()


class Warming(Exception):
    pass
