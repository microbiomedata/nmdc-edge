
test:
	PYTHONPATH=$(shell pwd) pytest --cov-report term --cov=nmdc_automation ./tests
