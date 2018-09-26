# Makefile executes first target if all is not specified
init:
	pip install pipenv --upgrade
	pipenv install --dev --skip-lock

test:
	scripts/ci
