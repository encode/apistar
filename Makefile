test:
	PYTHONPATH=. pytest --cov=apistar --cov-report xml --cov-report term tests
