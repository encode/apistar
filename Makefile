test:
	PYTHONPATH=. pytest tests

test-coverage:
	PYTHONPATH=. pytest --cov=apistar --cov-report xml --cov-report term tests