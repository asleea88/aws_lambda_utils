import pytest


@pytest.fixture(scope='function')
def sqs_event():
    sqs_event = {
        'Records': [
            {
                'eventSource': 'aws:sqs',
                'attributes': {},
                'messageId': 'messageId',
                'receiptHandle': 'receiptHandle',
                'body': None
            }
        ]
    }
    return sqs_event
