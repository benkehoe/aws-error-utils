# Changelog

`aws-error-utils` uses [monotonic versioning](blog.appliedcompscilab.com/monotonic_versioning_manifesto/).

## v2.5
* Fix type annotations.

## v2.4
* Require Python 3.6 as 3.5 is EOL.
* Update `AWSErrorInfo` to be a dataclass.
* Add type annotations ([#4](https://github.com/benkehoe/aws-error-utils/issues/4)).
    * Required refactoring from plain single-file module into package for `py.typed` file; single-file module within the package is [here](https://raw.githubusercontent.com/benkehoe/aws-error-utils/stable/aws_error_utils/aws_error_utils.py).

## v1.3
* Add `make_aws_error()` function for testing ([#5](https://github.com/benkehoe/aws-error-utils/issues/5)).

## v1.2
* Add `errors` class for simpler syntax (README.md#errors).

## v1.1
* `catch_aws_error()` adds `AWSErrorInfo` field to `ClientError`.
