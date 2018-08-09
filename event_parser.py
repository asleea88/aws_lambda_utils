import json
from logger import get_logger
from exceptions import InternalError, Warming
from abc import ABC


class EventParser(ABC):

    def __init__(self, event):
        self.logger = get_logger()
        self._event = event
        self.logger.debug('event: %s' % json.dumps(event, indent=4))
        self.is_warming(event)

    def is_warming(self, event):
        if 'source' in event and event['source'] == 'warmup':
            self.logger.debug('Warming lambda...')
            raise Warming


class HttpEventParser(EventParser):

    def __init__(self, event):
        super().__init__(event)
        self.size_alias = self._get_size_alias(event)
        self.img_key = self._get_img_key(event)
        self.accept = self._get_accept(event)

        self.logger.info(
            'EventParser: accept(%r), pathParameters(%r), queryString(%r)'
            % (self.accept, self.img_key, self.size_alias)
        )

    def _get_accept(self, event):
        return event['headers'].get('Accept', None)

    def _get_img_key(self, event):
        try:
            return event['pathParameters']['proxy']
        except KeyError as e:
            raise InternalError('There is no path parameter')

    def _get_size_alias(self, event):
        try:
            size_alias = event['queryStringParameters']['sa']

            self.qs = event['queryStringParameters']

            return size_alias.upper()

        except (KeyError, TypeError, AttributeError) as e:
            raise InternalError('Invalid size_alias is requseted.')


class HttpEventParser2(EventParser):

    def __init__(self, event):
        super().__init__(event)
        self.qs = event['queryStringParameters']


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
        self.records = []

        for record in event['Records']:
            self.records.append({
                'event_name': record['eventName'],
                'event_time': record['eventTime'],
                'bucket': record['s3']['bucket']['name'],
                'object_key': record['s3']['object']['key']
            })

        self.logger.info('EventParser: %s' % (self.records,))
