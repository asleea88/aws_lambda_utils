import boto3
from base64 import b64decode


class AWSClient:
    """
    Note:
        Seems not thread-safe
        Ref: https://github.com/boto/botocore/issues/1246
    """
    def __init__(self):
        self._client_dict = {}

    def __getitem__(self, key):
        try:
            aws_client = self._client_dict[key]
        except KeyError as e:
            aws_client = boto3.client(key)
            self._client_dict[key] = aws_client

        return aws_client

    def cwh_custom_err_metric(self, function_name):
        self['cloudwatch'].put_metric_data(
            MetricData=[
                {
                    'MetricName': 'Errors',
                    'Dimensions': [
                        {
                            'Name': 'FunctionName',
                            'Value': function_name
                        }
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                }
            ],
            Namespace='Lambda'
        )

    def ksm_decrypt(self, value):
        return self['kms'].decrypt(
            CiphertextBlob=b64decode(value)
        )['Plaintext'].decode()

    def sqs_delete_message(self, sqs_url, receipt_handle):
        self['sqs'].delete_message(
            QueueUrl=sqs_url,
            ReceiptHandle=receipt_handle
        )


aws_client = AWSClient()
