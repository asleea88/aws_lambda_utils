import functools
import time
import traceback
import os
import json
from .global_aws_client import aws_client
from .logger import get_logger
from .exceptions import ExceedMaximumRetry, UnexpectedError, PermanentError


class common_lambda_handler:
    """Common decorator for lambda_fucntion.
    """
    def __init__(self, dlq_url=None):
        self.dlq_url = dlq_url

    def __call__(self, func):

        @functools.wraps(func)
        def f(event, context):
            try:
                self.event = event
                self.context = context
                self.logger = get_logger('%s' % context.aws_request_id, True)
                self.logger.debug('event: %s' % json.dumps(event, indent=4))

                if self._is_warming(event):
                    return

                rtn = func(event, context)

            except Exception as e:
                err_msg = 'Lambda Error(%s) - %s' % (
                    context.aws_request_id, traceback.format_exc()
                )

                if issubclass(e.__class__, PermanentError):
                    self.logger.error(err_msg)
                    self._handle_permanent_err()
                    return

                # If an exception is not PermanentError,
                #   it will just raise the error.
                #   when it comes to Asynchronous event,
                #   the error will be retried twice by AWS.
                raise Exception(err_msg)

            return rtn

        return f

    def _handle_permanent_err(self):
        """
        It counts PermanentError Metric.
        If DLQ is set, It puts the event into the DLQ.
        """
        aws_client.cwh_custom_metric(
            self.context.function_name, 'PermanentError',
            unit='Count', value=1
        )

        if self.dlq_url is None:
            return

        # TODO: If an error happens while sending a message to DLQ?
        aws_client.send_message(
            QueueUrl=self.dlq_url, MesssageBody=json.dumps(self.event)
        )

    def _is_warming(self, event):
        if 'source' in event and event['source'] == 'warmup':
            self.logger.debug('Warming lambda...')
            return True
        return False


class sqs_delete_message:
    """
    SQS Message is deleted only
        when lambda ends with no error(if DLQ is not set).
        if user doens't delete the message manually,
        it will keep trying infinitly.

    Sometime, user doens't want lambda to retry against specific error.
        The class would hlep your demand.
    """
    def __init__(self, receipt_handle, exp_list=(Exception, )):
        self.logger = get_logger()
        self.exp_list = exp_list
        self.receipt_handle = receipt_handle

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if issubclass(exc_type, self.exp_list):
            self._handle_excption()

    def __call__(self, func):
        @functools.wraps(func)
        def f(event, context):
            try:
                rtn = func(event, context)

            except self.exp_list as e:
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
    """
    Many AWS resources have limits for sort of request per XXX.
        It forces user to split a list into several small list.
        The method is for the case.
    """

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
