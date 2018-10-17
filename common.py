from .logger import get_logger
from .exceptions import Warming
from .global_aws_client import aws_client


class common_lambda_handler:

    def __init__(self, exp_propagate=True, custom_error_metric=False):
        self.exp_propagate = exp_propagate
        self.custom_error_metric = custom_error_metric

    def __call__(self, func):

        def f(event, context):
            try:
                logger = get_logger('%s' % context.aws_request_id, True)
                rtn = func(event, context)

            except Warming as e:
                return

            except Exception as e:
                logger.exception(e)

                if self.custom_error_metric:
                    aws_client.cwh_custom_err_metric(context.function_name)

                if not self.exp_propagate:
                    return

                raise Exception(
                    'Lambda Error(%s, %s)'
                    % (context.aws_request_id, e.__class__.__name__)
                )

            return rtn

        return f
