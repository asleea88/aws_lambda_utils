import functools
import traceback
from .logger import get_logger
from .exceptions import Warming, ExceedMaximumRetry, UnexpectedError


def retry_against_exception(func, max_num=3, exp_list=(Exception, )):

    @functools.wraps(func)
    def f(*args, **kwargs):
        for i in range(1, max_num+1):
            try:
                return func(*args, **kwargs)

            except exp_list as e:
                get_logger().error(
                    'Retry Count(%s): %s' % (i, traceback.format_exc())
                )

                if i >= max_num:
                    # When reaching the maximum number of retry.
                    get_logger().warning(
                        'Escape retry loop after %s try' % max_num
                    )
                    raise ExceedMaximumRetry(
                        'Exceed the maximum number of retry(%s)' % max_num
                    )

        raise UnexpectedError('Unexpected error, it MUST not be printed')

    return f


class common_lambda_handler:

    def __init__(self, exp_propagate=True):
        self.exp_propagate = exp_propagate

    def __call__(self, func):

        @functools.wraps(func)
        def f(event, context):
            try:
                logger = get_logger('%s' % context.aws_request_id, True)
                rtn = func(event, context)

            except Warming as e:
                return

            except Exception as e:
                logger.exception(e)

                if not self.exp_propagate:
                    return

                raise Exception(
                    'Lambda Error(%s, %s)'
                    % (context.aws_request_id, e.__class__.__name__)
                )

            return rtn

        return f
