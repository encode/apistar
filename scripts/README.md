# Development Scripts

You may need to install ["poetry"](https://poetry.eustace.io/) first.


* `scripts/setup` - Create a virtualenv directory, and install the dev requirements.
* `scripts/test` - Run the API Star test suite, using `py.test`.
* `scripts/lint` - Run `flake8` and `isort` against the code and tests.
* `scripts/ci` - Run the tests and linting with correct options for continuous integration.
* `scripts/publish` - Publish the latest version to PyPI. (Requires maintainer permissions.)

Styled after GitHub's ["Scripts to Rule Them All"](https://github.com/github/scripts-to-rule-them-all).
