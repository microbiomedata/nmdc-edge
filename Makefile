
test:
	PYTHONPATH=$(shell pwd) pytest --cov-report term --cov-report html --cov=nmdc_automation ./tests
