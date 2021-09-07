# aws-error-utils
**Making botocore.exceptions.ClientError easier to deal with**

All AWS service exceptions are raised by `boto3` as a `botocore.exceptions.ClientError`, with the contents of the exception indicating what kind of exception happened.
This is not very pythonic, and the contents themselves are rather opaque, most being held in dicts rather than as properties.
The functions in this package help dealing with that, to make your code less verbose and require less memorization of `ClientError` contents.

## Installation

[The package is on PyPI](https://pypi.org/project/aws-error-utils/) for pip-installing, but I tend to prefer just copying the [`aws_error_utils.py` file](https://raw.githubusercontent.com/benkehoe/aws-error-utils/master/aws_error_utils.py) into my projects; often then my only dependency is on `boto3`, which is usually somewhere in my environment anyway (e.g., in a Lambda function). But that's just me.

## Usage
If you've got code like this:

```python
s3 = boto3.client('s3')
try:
    s3.get_object(Bucket='my-bucket', Key='example')
except botocore.ClientError as error:
    if error.response['Error']['Code'] == 'NoSuchBucket':
        print(error.response['Error']['Message'])
        # error handling
    else:
        raise
```

you can replace it with:

```python
import boto3
from aws_error_utils import errors

s3 = boto3.client('s3')
try:
    s3.get_object(Bucket='my-bucket', Key='example')
except errors.NoSuchBucket as error:
    print(error.message)
    # error handling
```

If you have trouble remembering where all the contents in `ClientError` are, like these:

```python
client_error.response['Error']['Code']
client_error.response['Error']['Message']
client_error.response['ResponseMetadata']['HTTPStatusCode']
client_error.operation_name
```

you can replace it with:

```python
import boto3
from aws_error_utils import get_aws_error_info

err_info = get_aws_error_info(client_error)

err_info.code
err_info.message
err_info.http_status_code
err_info.operation_name
```

If you're using `errors` or `catch_aws_error()`, you can skip the `get_aws_error_info()` step, because the fields are set directly on the `ClientError` object:

```python
import boto3
from aws_error_utils import errors

s3 = boto3.client('s3')
try:
    s3.get_object(Bucket='my-bucket', Key='example')
except errors.NoSuchBucket as error:
    error.code
    error.message
    error.http_status_code
    error.operation_name
```

## `errors`
It's easiest to use the `errors` class if you don't have complex conditions to match.
Using the error code as a field name in an `except` block will match that error code.
Additionally, when you use this style, it sets the fields from `AWSErrorInfo` (see below) directly on the `ClientError` object.
For example:

```python
import boto3
from aws_error_utils import errors

s3 = boto3.client('s3')
try:
    s3.get_object(Bucket='my-bucket', Key='example')
except errors.NoSuchBucket as error:
    print(error.message)

    # error handling
```

You can include multiple error codes in an `except` statement, though this is slower than combining them with a single `catch_aws_error()` call.

```python
import boto3
from aws_error_utils import errors

s3 = boto3.client('s3')
try:
    s3.get_object(Bucket='my-bucket', Key='example')
except (errors.NoSuchBucket, errors.NoSuchKey) as error:
    print(error.message)

    # error handling
```

You can only use this style for error codes that work as Python property names.
For error codes like EC2's `InvalidInstanceID.NotFound`, you have to use `catch_aws_error()` (see below).

Unfortunately, you cannot get tab completion for error codes on the `errors` class, as a comprehensive list of error codes is not available as a Python package (`botocore` has a small number, but they are few and incomplete).

Note that the value of `errors.NoSuchBucket` is not an exception class representing the `NoSuchBucket` error, it is an alias for `catch_aws_error('NoSuchBucket')`.
It can only be used in an `except` statement; it will raise `RuntimeError` otherwise.
You also cannot instantiate the `errors` class.

## `catch_aws_error()`
The function takes as input error code(s), and optionally operation name(s), to match against the current raised exception. If the exception matches, the `except` block is executed.
If your error handling still needs the error object, you can still use an `as` expression, otherwise it can be omitted (just `except catch_aws_error(...):`).
Additionally, `catch_aws_error()` sets the fields from `AWSErrorInfo` (see below) directly on the `ClientError` object.

```python
import boto3
from aws_error_utils import catch_aws_error

s3 = boto3.client('s3')
try:
    s3.get_object(Bucket='my-bucket', Key='example')
except catch_aws_error('NoSuchBucket') as error:
    print(error.message)

    # error handling
```

You can provide error codes either as positional args, or as the `code` keyword argument with either as a single string or a list of strings.

```python
catch_aws_error('NoSuchBucket')
catch_aws_error(code='NoSuchBucket')

catch_aws_error('NoSuchBucket', 'NoSuchKey')
catch_aws_error(code=['NoSuchBucket', 'NoSuchKey'])
```

If there are multiple API calls in the `try` block, and you want to match against specific ones, the `operation_name` keyword argument can help.
Similar to the `code` keyword argument, the operation name(s) can be provided as either as a single string or a list of strings.

```python
import boto3
from aws_error_utils import catch_aws_error

try:
    s3 = boto3.client('s3')
    s3.list_objects_v2(Bucket='bucket-1')
    s3.get_object(Bucket='bucket-2', Key='example')
except catch_aws_error('NoSuchBucket', operation_name='GetObject') as error:
    # This will be executed if the GetObject operation raises NoSuchBucket
    # but not if the ListObjects operation raises it
```

You must provide an error code.
To match exclusively against operation name, use the `aws_error_utils.ALL_CODES` token.
For completeness, there is also an `ALL_OPERATIONS` token.

```python
import boto3
from aws_error_utils import catch_aws_error

try:
    s3 = boto3.client('s3')
    s3.list_objects_v2(Bucket='bucket-1')
    s3.get_object(Bucket='bucket-1', Key='example')
except catch_aws_error(ALL_CODES, operation_name='ListObjectsV2') as e:
    # This will execute for all ClientError exceptions raised by the ListObjectsV2 call
```

For more complex conditions, instead of providing error codes and operation names, you can provide a callable to evaluate the exception.
Note that unlike error codes, you can only provide a single callable.

```python
import re
import boto3
from aws_error_utils import catch_aws_error, get_aws_error_info

def matcher(e):
    info = get_aws_error_info(e)
    return re.search('does not exist', info.message)

try:
    s3 = boto3.client('s3')
    s3.list_objects_v2(Bucket='bucket-1')
except catch_aws_error(matcher) as e:
    # This will be executed if e is a ClientError and matcher(e) returns True
    # Note the callable can assume the exception is a ClientError
```

## `get_aws_error_info()`
This function takes a returns an `AWSErrorInfo` object, which is a `collections.NamedTuple` with the following fields:

* `code`
* `message`
* `http_status_code`
* `operation_name`
* `response` (the raw response dictionary)

If you're not modifying your `except` statements to use `catch_aws_error()`, this function can be useful instead of remembering exactly how this information is stored in the `ClientError` object.

If you're using `catch_aws_error()`, this function isn't necessary, because it sets these fields directly on the `ClientError` object.

## `aws_error_matches()`
This is the matching logic behind `catch_aws_error()`.
It takes a `ClientError`, with the rest of the arguments being error codes and operation names identical to `catch_aws_error()`, except that it does not support providing a callable.
