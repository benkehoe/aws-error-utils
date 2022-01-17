# Copyright 2020 Ben Kehoe and aws-error-utils contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Helpful snippets:
error_code = e.response.get('Error', {}).get('Code')
error_msg = e.response.get('Error', {}).get('Message')
status_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode')
operation_name = e.operation_name
"""

__version__ = '1.3.0' # update here and pyproject.toml

import collections
import sys

from botocore.exceptions import BotoCoreError, ClientError

__all__ = [
    'AWSErrorInfo',
    'get_aws_error_info',
    'ALL_CODES',
    'ALL_OPERATIONS',
    'aws_error_matches',
    'catch_aws_error',
    'BotoCoreError',
    'ClientError',
    'errors',
    'make_aws_error',
]

AWSErrorInfo = collections.namedtuple('AWSErrorInfo', ['code', 'message', 'http_status_code', 'operation_name', 'response'])
def get_aws_error_info(client_error):
    """Returns an AWSErrorInfo namedtuple with the important details of the error extracted"""
    if not isinstance(client_error, ClientError):
        raise TypeError("Error is of type {}, not ClientError".format(client_error))
    return AWSErrorInfo(
            client_error.response.get('Error', {}).get('Code'),
            client_error.response.get('Error', {}).get('Message'),
            client_error.response.get('ResponseMetadata', {}).get('HTTPStatusCode'),
            client_error.operation_name,
            client_error.response,
    )

ALL_CODES = "__aws_error_utils_ALL_CODES__"
ALL_OPERATIONS = "__aws_error_utils_ALL_OPERATIONS__"

def aws_error_matches(client_error, *args, **kwargs):
    """Tests if a botocore.exceptions.ClientError matches the arguments.

    Any positional arguments and the contents of the 'code' kwarg are matched
    against the Error.Code response field.
    If the 'operation_name' kwarg is provided, it is matched against the
    operation_name property.
    Both kwargs can either be a single string or a list of strings.
    The tokens aws_error_utils.ALL_CODES and aws_error_utils.ALL_OPERATIONS
    can be used to match all error codes and operation names.

    try:
        s3 = boto3.client('s3')
        s3.list_objects_v2(Bucket='bucket-1')
        s3.get_object(Bucket='bucket-2', Key='example')
    except botocore.exceptions.ClientError as e:
        if aws_error_matches(e, 'NoSuchBucket', operation_name='GetObject'):
            pass
        else:
            raise
    """
    if not isinstance(client_error, ClientError):
        raise TypeError("Error is of type {}, not ClientError".format(type(client_error)))
    err_args = args + tuple((kwargs.get('code'),) if isinstance(kwargs.get('code'), str) else kwargs.get('code', tuple()))
    op_args = (kwargs.get('operation_name'),) if isinstance(kwargs.get('operation_name'), str) else kwargs.get('operation_name', tuple())
    if not err_args:
        raise ValueError('No error codes provided')
    err = client_error.response.get('Error', {}).get('Code')
    err_matches = (err and (err in err_args)) or (ALL_CODES in err_args)
    op_matches = (client_error.operation_name in op_args) or (not op_args) or (ALL_OPERATIONS in op_args)
    return err_matches and op_matches

def catch_aws_error(*args, **kwargs):
    """For use in an except statement, returns the current error's type if it matches the arguments, otherwise a non-matching error type

    Any positional arguments and the contents of the 'code' kwarg are matched
    against the Error.Code response field.
    If the 'operation_name' kwarg is provided, it is matched against the
    operation_name property.
    Both kwargs can either be a single string or a list of strings.
    The tokens aws_error_utils.ALL_CODES and aws_error_utils.ALL_OPERATIONS
    can be used to match all error codes and operation names.
    Alternatively, provide a callable that takes the error and returns true for a match.

    If the error matches, the fields from AWSErrorInfo are set on the ClientError object.

    try:
        s3 = boto3.client('s3')
        s3.list_objects_v2(Bucket='bucket-1')
        s3.get_object(Bucket='bucket-2', Key='example')
    except catch_aws_error('NoSuchBucket', operation_name='GetObject') as error:
        # error handling
    """
    # (type, value, traceback)
    exc_info = sys.exc_info()
    if not exc_info[0]:
        raise RuntimeError("You must use catch_aws_error() inside an except statement")

    client_error = exc_info[1]
    matched = False
    if isinstance(client_error, ClientError):
        if len(args) == 1 and callable(args[0]):
            if args[0](client_error):
                matched = True
        elif aws_error_matches(client_error, *args, **kwargs):
            matched = True
    if matched:
        err_info = get_aws_error_info(client_error)
        for key, value in err_info._asdict().items():
            if not hasattr(client_error, key):
                setattr(client_error, key, value)
        # return the error class, which will cause a match
        return exc_info[0]
    else:
        # this dynamically-generated type can never match a raised exception
        return type('RedHerring', (BaseException,), {})

# Use a metaclass to hook into field access on the class
class _ErrorsMeta(type):
    def __getattr__(self, name):
        if not sys.exc_info()[0]:
            raise RuntimeError("You must use {}.{} inside an except statement".format(self.__name__, name))
        return catch_aws_error(name)

class errors(metaclass=_ErrorsMeta):
    """Fields on this class used in `except` blocks match ClientErrors with an error code equal to the field name.

    The value of the field is not a type. Instead, the field access calls catch_aws_error() with the field name.

    This class cannot be instantiated.

    try:
        s3 = boto3.client('s3')
        s3.get_object(Bucket='my-bucket', Key='example')
    except errors.NoSuchBucket as error:
        # error handling
    """
    def __init__(self):
        raise RuntimeError("{} cannot be instantiated".format(self.__class__.__name__))

def make_aws_error(code, message, operation_name, http_status_code=None, response=None) -> ClientError:
    """Create a ClientError using the given information, useful for testing.

    If you have an AWSErrorInfo object, you can use it with this function:
    make_aws_error(**my_error_info._asdict())
    """
    if response is None:
        response = {}
    else:
        response = response.copy()
    if code or message:
        response["Error"] = {}
    if code:
        response["Error"]["Code"] = code
    if message:
        response["Error"]["Message"] = message
    if http_status_code:
        if "ResponseMetadata" not in response:
            response["ResponseMetadata"] = {}
        else:
            response["ResponseMetadata"] = response["ResponseMetadata"].copy()
        response["ResponseMetadata"]["HTTPStatusCode"] = http_status_code
    return ClientError(response, operation_name)
