from .logger import get_logger
from .exceptions import Warming


def common_lambda_handler(func):

    def f(event, context):
        try:
            logger = get_logger('%s' % context.aws_request_id, True)
            rtn = func(event, context)

        except Warming as e:
            return

        except Exception as e:
            logger.exception(e)
            raise Exception(
                'Lambda Error(%s, %s)'
                % (context.aws_request_id, e.__class__.__name__)
            )

        return rtn

    return f
