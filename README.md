# aws-error-utils
**Making botocore.exceptions.ClientError easier to deal with**

All AWS service exceptions are raised by `boto3` as a `ClientError`, with the contents of the exception indicating what kind of exception happened.
This is not very pythonic, and the contents themselves are rather opaque, being held in a dict rather than as properties.
The functions in this package help dealing with that.

The package is on PyPI but I tend to prefer just copying the `aws_error_utils.py` file into my projects, often then my only dependency is on boto3, which is usually somewhere in my environment anyway (e.g., in a Lambda function). But that's just me.

## `catch_aws_error()`
This is probably the most useful function in the package. Make exception catching more natural. You use this function in an `except` statement instead of `ClientError`. The function takes as input error code(s), and optionally operation name(s), to match against the current raised exception. If the exception matches, the `except` block is executed. Usage looks like this:

```python
try:
    s3 = boto3.client('s3')
    s3.list_objects_v2(Bucket='bucket-1')
    s3.get_object(Bucket='bucket-2', Key='example')
except catch_aws_error('NoSuchBucket', operation_name='GetObject'):
    # This will be executed if the GetObject operation raises NoSuchBucket
    # But not if the ListObjects operation raises it
```

You can provide error codes either as positional args or as the `code` keyword argument, and there either as a single string or a list of strings.

```python
catch_aws_error('NoSuchBucket')
catch_aws_error(code='NoSuchBucket')

catch_aws_error('NoSuchBucket', 'NoSuchKey')
catch_aws_error(code=['NoSuchBucket', 'NoSuchKey'])
```

The operation name can only be provided as the `operation_name` keyword argument, but similarly either as a single string or a list of strings.

You must provide an error code. To match exclusively against operation name, use the `aws_error_utils.ALL_CODES` token. There is similarly an `ALL_OPERATIONS` token.

```python
try:
    s3 = boto3.client('s3')
    s3.list_objects_v2(Bucket='bucket-1')
    s3.get_object(Bucket='bucket-1', Key='example')
except catch_aws_error(ALL_CODES, operation_name='ListObjectsV2') as e:
    # This will execute for all ClientError exceptions raised by the ListObjectsV2 call
```

For more complex conditions, instead of providing error codes and operation names, you can provide a callable to evaluate the exception:

```python
import re
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
This function takes a returns an `AWSErrorInfo` object, which is a `collections.NamedTuple` with the error code, error message, HTTP status code, and operation name extracted, along with the raw response dictionary. If you're not modifying your code's exception handling, this can be useful instead of remembering exactly how the error code is stored in the response, etc.

## `aws_error_matches()`
This is the matching logic behind `catch_aws_error()`. It takes a `ClientError`, with the rest of the arguments being error codes and operation names identical to `catch_aws_error`, except that it does not support providing a callable.
