import pytest
from unittest import mock
from ..common import common_lambda_handler
from ..common import retry_against_exception
from ..exceptions import ExceedMaximumRetry, PermanentError


class Context:
    aws_request_id = 'pytest'
    function_name = 'function_name'


def inner_func(event, context):
    if event == 'Exception':
        raise Exception()
    elif event == 'PermanentError':
        raise PermanentError()

    return event


inner_func1 = common_lambda_handler()(inner_func)
inner_func2 = common_lambda_handler('dlq')(inner_func)


def test_common_lambda_handler():

    inner_func1 = common_lambda_handler()(inner_func)

    # propagation
    rtn = inner_func1({'source': 'pytest'}, Context)
    assert rtn == {'source': 'pytest'}

    with pytest.raises(Exception):
        inner_func1('Exception', Context)


def test_common_lambda_handler_pemanent_error():

    with mock.patch.object(
        common_lambda_handler, '_handle_permanent_err'
    ) as m:
        inner_func1 = common_lambda_handler()(inner_func)
        inner_func1('PermanentError', Context)
        m.assert_called_once()

    with mock.patch.object(
        common_lambda_handler, '_handle_permanent_err'
    ) as m:
        inner_func2 = common_lambda_handler('dlq')(inner_func)
        inner_func2('PermanentError', Context)
        m.assert_called_once()


def test_retry_against_excpetion1():

    func_mock = mock.MagicMock(
        side_effect=[Exception, Exception, {'source': 'pytest'}]
    )
    retry_func_mock = retry_against_exception(func_mock, 3)
    rtn = retry_func_mock()
    assert rtn == {'source': 'pytest'}


def test_retry_against_excpetion2():
    func_mock = mock.MagicMock(side_effect=[Exception, Exception, KeyError])
    retry_func_mock = retry_against_exception(
        func_mock, 3, (Exception, KeyError)
    )
    with pytest.raises(ExceedMaximumRetry):
        retry_func_mock()


def test_retry_against_excpetion3():
    func_mock = mock.MagicMock(side_effect=[TypeError, Exception])
    retry_func_mock = retry_against_exception(
        func_mock, 3, (KeyError, TypeError)
    )
    with pytest.raises(Exception):
        retry_func_mock()
