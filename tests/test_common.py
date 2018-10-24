import pytest
from unittest import mock
from ..common import common_lambda_handler
from ..common import retry_against_exception


class Context:
    aws_request_id = 'pytest'


def inner_func(event, context):
    if event == 'exception':
        raise Exception()

    return event


inner_func1 = common_lambda_handler()(inner_func)
inner_func2 = common_lambda_handler(False)(inner_func)


def test_common_lambda_handler():

    # propagation
    rtn = inner_func1(10, Context)
    assert rtn == 10

    with pytest.raises(Exception):
        inner_func1('exception', Context)

    # No propagation
    rtn = inner_func2(10, Context)
    assert rtn == 10

    inner_func2('exception', Context)


def test_retry_against_excpetion():

    func_mock = mock.MagicMock(side_effect=[Exception, Exception, 10])
    retry_func_mock = retry_against_exception(func_mock, 3)
    rtn = retry_func_mock()
    assert rtn == 10

    func_mock = mock.MagicMock(side_effect=[Exception, Exception, KeyError])
    retry_func_mock = retry_against_exception(func_mock, 3)

    with pytest.raises(KeyError):
        rtn = retry_func_mock()
