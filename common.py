from .logger import get_logger
from .exceptions import Warming


class common_lambda_handler:

    def __init__(self, exp_propagate=True):
        self.exp_propagate = exp_propagate

    def __call__(self, func):

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
