
test:
	PYTHONPATH=$(shell pwd) pytest --cov-report term --cov-report html --cov=src
