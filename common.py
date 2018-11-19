import functools
import time
import traceback
import os
import json
from .global_aws_client import aws_client
from .logger import get_logger
from .exceptions import ExceedMaximumRetry, UnexpectedError


class common_lambda_handler:
    """Common decorator for lambda_fucntion.

    It Initializes logger named `aws_request_id` and catch Warming exception.
    """
    def __init__(self, excp_propagate=True):
        """
        Args:
            excep_propagate: Flag if the exception should be progataed or not.
                If an exception is propagated to out of the lambda function,
                It will be counted in CloudWatch `Error` metric and could be
                retried depending on evnet source.
        """
        self.excp_propagate = excp_propagate

    def __call__(self, func):

        @functools.wraps(func)
        def f(event, context):
            try:
                self.logger = get_logger('%s' % context.aws_request_id, True)
                self.logger.debug('event: %s' % json.dumps(event, indent=4))

                if self.is_warming(event):
                    return

                rtn = func(event, context)

            except Exception as e:
                self.logger.exception(e)

                if not self.excp_propagate:
                    return

                raise Exception(
                    'Lambda Error(%s, %s)'
                    % (context.aws_request_id, e.__class__.__name__)
                )

            return rtn

        return f

    def is_warming(self, event):
        if 'source' in event and event['source'] == 'warmup':
            self.logger.debug('Warming lambda...')
            return True
        return False


class sqs_delete_message:
    def __init__(self, receipt_handle):
        self.logger = get_logger()
        self.receipt_handle = receipt_handle

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if traceback is not None:
            self._handle_excption()

    def __call__(self, func):
        @functools.wraps(func)
        def f(event, context):
            try:
                rtn = func(event, context)

            except Exception as e:
                self._handle_excption()
                raise e

            return rtn

        return f

    def _handle_excption(self):
        aws_client.sqs_delete_message(
            os.environ['SQS_URL'], self.receipt_handle
        )
        self.logger.info('Delete message from SQS')


def iter_partial_list(target_list, split_num):
    partial_num_list = [
        x for x in range(0, len(target_list), split_num)
    ]
    for n in partial_num_list:
        yield target_list[n:n+split_num]


def make_sure_list(target):
    if not isinstance(target, list):
        target = [target]
    return target


def retry_against_exception(
    func, retry_num=2, excp_list=(Exception, ), interval=2
):
    """Common retry decorator against exceptions.

    Args:
        func: Function to be retried.
        retry_num: The maximum number of retry.
        excp_list: Target to catch exception and retry.
        interval: Interval between retries.
    """

    @functools.wraps(func)
    def f(*args, **kwargs):
        for i in range(retry_num+1):
            req_cnt = i + 1
            try:
                return func(*args, **kwargs)

            except excp_list as e:
                get_logger().error(
                    'Request Count(%s): %s' % (req_cnt, traceback.format_exc())
                )

                if i >= retry_num:
                    # When reaching the maximum number of retry.
                    get_logger().warning(
                        'Escape retry loop after %s try' % retry_num
                    )
                    raise ExceedMaximumRetry(
                        'Exceed the maximum number of retry(%s)' % retry_num
                    )

                time.sleep(interval * req_cnt)

        raise UnexpectedError('Unexpected error, it MUST not be printed')

    return f
