import json
from .logger import get_logger
from .exceptions import Warming, InternalError
from abc import ABC


class EventParser(ABC):

    def __init__(self, event):
        self.logger = get_logger()
        self.records = []
        self._event = event
        self.logger.debug('event: %s' % json.dumps(event, indent=4))
        self.is_warming(event)

    def is_warming(self, event):
        if 'source' in event and event['source'] == 'warmup':
            self.logger.debug('Warming lambda...')
            raise Warming


class S3EventParser(EventParser):
    """
    event_name
    object_key
    bucket_name
    """

    def __init__(self, event):
        """
        TODO:
            * More than one `Record` could be sent?
        """
        super().__init__(event)

        for record in event['Records']:
            self.records.append({
                'event_name': record['eventName'],
                'event_time': record['eventTime'],
                'bucket': record['s3']['bucket']['name'],
                'object_key': record['s3']['object']['key']
            })

        self.logger.info('%s: %s' % (self.__class__.__name__, self.records,))


class SnsEventParser(EventParser):

    SUBJECT_TYPE = {
        'Amazon S3 Notification': S3EventParser
    }

    def __init__(self, event, pub):
        super().__init__(event)

        for record in event['Records']:

            if record['Sns']['Subject'] not in self.SUBJECT_TYPE.keys():
                self.logger.warning(
                    'Unexpected SNS Subject(%s)' % record['Sns']['Subject']
                )
                continue

            json_msg = json.loads(record['Sns']['Message'])

            self.records.extend(
                self.SUBJECT_TYPE[record['Sns']['Subject']](json_msg).records
            )

        self.logger.info('%s: %s' % (self.__class__.__name__, self.records,))


###############################################################################
# Event Source
###############################################################################

class EventSource():

    def __init__(self, record):
        self._raw_record = record
        self.event_src = self.__class__.__name__
        self.logger = get_logger()

    def log_source(self, as_debug=False):
        if as_debug:
            self.logger.debug(
                '%s: %s' % (self.__class__.__name__, self._record)
            )
        else:
            self.logger.info(
                '%s: %s' % (self.__class__.__name__, self._record)
            )

    def __getitem__(self, key):
        return self._record[key]

    def __str__(self):
        return str(self._record)


class S3EventSource(EventSource):

    def __init__(self, record):
        super().__init__(record)

        self._record = {
            'event_name': record['eventName'],
            'event_time': record['eventTime'],
            'bucket': record['s3']['bucket']['name'],
            'object_key': record['s3']['object']['key']
        }
        self.log_source()


class SqsEventSource(EventSource):

    def __init__(self, record):
        super().__init__(record)

        self._record = {
            'body': record['body'],
            'attributes': record['attributes'],
            'messageId': record['messageId'],
            'receiptHandle': record['receiptHandle']
        }
        self.logger.info('receiptHandler: %s' % record['receiptHandle'])
        self.log_source(True)


class SnsEventSource(EventSource):

    def __init__(self, record):
        super().__init__(record)

        self._record = {
            'message': record['Sns']['Message'],
            'subject': record['Sns']['Subject']
        }
        self.json_msg = json.loads(self._record['message'])
        self.log_source()

    def get_sub_record(self):
        parser = AsyncEventParser(self.json_msg)
        return parser.records

    def log_source(self):
        if 'Records' in self.json_msg:
            n = len(self.json_msg['Records'])
        else:
            n = 0  # When new notification is added.

        self.logger.info(
            '%s: inner message(%s)'
            % (self.__class__.__name__, n)
        )


class AsyncEventParser(EventParser):

    def __init__(self, event):
        super().__init__(event)
        self._event = event
        self.records = {
            's3': [],
            'sns': [],
            'sqs': []
        }

        try:
            for record in self._event['Records']:
                self.__handler(record)
        except KeyError:
            raise InternalError('NoRecord')

        self.logger.debug(
            '%s: %s' % (self.__class__.__name__, self.records)
        )

    def __handler(self, record):
        if 'EventSource' in record:
            event_src = record['EventSource']
        elif 'eventSource' in record:
            event_src = record['eventSource']
        else:
            assert None

        if event_src == 'aws:s3':
            self.records['s3'].append(S3EventSource(record))

        elif event_src == 'aws:sns':
            self.records['sns'].append(SnsEventSource(record))

        elif event_src == 'aws:sqs':
            self.records['sqs'].append(SqsEventSource(record))

    def get_records(self):
        """
        Summary:
           In order for compatibility between direct S3 event
           and proxy S3 event(SNS).
        """
        records = []

        records.extend(self.records['s3'])

        for sns_record in self.records['sns']:
            records.extend(
                sns_record.get_sub_record()['s3']
            )

        return records
