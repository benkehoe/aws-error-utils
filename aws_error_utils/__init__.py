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

from .aws_error_utils import (
    __version__ as __version__,
    AWSErrorInfo as AWSErrorInfo,
    get_aws_error_info as get_aws_error_info,
    ALL_CODES as ALL_CODES,
    ALL_OPERATIONS as ALL_OPERATIONS,
    aws_error_matches as aws_error_matches,
    catch_aws_error as catch_aws_error,
    BotoCoreError as BotoCoreError,
    ClientError as ClientError,
    errors as errors,
    make_aws_error as make_aws_error,
)
