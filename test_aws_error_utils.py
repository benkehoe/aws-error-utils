# Copyright 2020 Ben Kehoe
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

import pytest
import re
import uuid

from botocore.exceptions import ClientError

from aws_error_utils import get_aws_error_info, aws_error_matches, catch_aws_error, ALL_CODES, ALL_OPERATIONS, errors

def make_error(operation_name, code=None, message=None, http_status_code=None, error=True):
    response = {}
    if error or code or message:
        response['Error'] = {}
    if code:
        response['Error']['Code'] = code
    if message:
        response['Error']['Message'] = message
    if http_status_code:
        response['ResponseMetadata'] = {'HTTPStatusCode': http_status_code}
    return ClientError(response, operation_name)

def test_create_error_info():
    error = make_error('AssumeRole', 'RegionDisabled',  http_status_code=403)
    error_info = get_aws_error_info(error)
    assert error_info.code == 'RegionDisabled'
    assert error_info.operation_name == 'AssumeRole'
    assert error_info.http_status_code == 403
    assert error_info.message is None

    not_error = ValueError('not a ClientError')
    with pytest.raises(TypeError):
        get_aws_error_info(not_error)

def test_error_info_missing_code():
    error = make_error('AssumeRole')
    error_info = get_aws_error_info(error)
    assert error_info.code is None

def test_error_matches_requries_code():
    with pytest.raises(ValueError, match='No error codes provided'):
        error = make_error('AssumeRole', 'RegionDisabled')
        aws_error_matches(error)

    with pytest.raises(ValueError, match='No error codes provided'):
        error = make_error('AssumeRole', 'RegionDisabled')
        aws_error_matches(error, operation_name='AssumeRole')

def test_error_matches_single():
    error = make_error('AssumeRole', 'RegionDisabled')
    assert aws_error_matches(error, 'RegionDisabled')
    assert aws_error_matches(error, 'RegionDisabled', 'OtherCode')
    assert aws_error_matches(error, 'RegionDisabled', code='OtherCode')
    assert aws_error_matches(error, 'RegionDisabled', code=['OtherCode'])
    assert aws_error_matches(error, 'OtherCode', code='RegionDisabled')
    assert aws_error_matches(error, 'OtherCode', code=['RegionDisabled'])

    assert not aws_error_matches(error, 'OtherCode')
    assert not aws_error_matches(error, code='OtherCode')
    assert not aws_error_matches(error, code=['OtherCode'])

    assert aws_error_matches(error, 'RegionDisabled', operation_name='AssumeRole')
    assert aws_error_matches(error, 'RegionDisabled', operation_name=['AssumeRole', 'OtherOp'])
    assert not aws_error_matches(error, 'RegionDisabled', operation_name='OtherOp')

def test_error_matches_all():
    code = str(uuid.uuid4())
    error = make_error('OpName', code)

    assert aws_error_matches(error, ALL_CODES)
    assert not aws_error_matches(error, 'SpecificCode')

    op_name = str(uuid.uuid4())
    error = make_error(op_name, 'SomeCode')

    assert aws_error_matches(error, 'SomeCode', operation_name=ALL_OPERATIONS)
    assert not aws_error_matches(error, 'SomeCode', operation_name='SpecificOperation')

def test_catch():
    error = make_error('AssumeRole', 'RegionDisabled')
    try:
        raise error
    except catch_aws_error('RegionDisabled') as e:
        assert e is error

    with pytest.raises(ClientError, match=re.escape(str(error))):
        try:
            raise error
        except catch_aws_error('OtherCode') as e:
            assert False

    def matcher(client_error):
        return client_error is error

    try:
        raise error
    except catch_aws_error(matcher) as e:
        assert e is error

    def nonmatcher(client_error):
        return False

    with pytest.raises(ClientError, match=re.escape(str(error))):
        try:
            raise error
        except catch_aws_error(nonmatcher) as e:
            assert False

    class OtherError(Exception):
        pass

    try:
        raise OtherError('test')
    except catch_aws_error(ALL_CODES) as e:
        assert False
    except OtherError:
        assert True

def test_catch_sets_info():
    operation_name = str(uuid.uuid4())
    code = str(uuid.uuid4())
    message = str(uuid.uuid4())
    http_status_code = 404
    error = make_error(operation_name, code=code, message=message, http_status_code=http_status_code)

    try:
        raise error
    except catch_aws_error(code) as error:
        assert error.operation_name == operation_name
        assert error.code == code
        assert error.message == message
        assert error.http_status_code == http_status_code

def test_errors():
    error = make_error('AssumeRole', 'RegionDisabled',  http_status_code=403)

    try:
        raise error
        assert False
    except errors.RegionDisabled:
        pass

    try:
        raise error
        assert False
    except (errors.NoSuchRegion, errors.RegionDisabled):
        pass

    with pytest.raises(RuntimeError):
        errors.RegionDisabled

    with pytest.raises(RuntimeError):
        errors()
