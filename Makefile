
test:
	poetry run pytest --cov-report term --cov=nmdc_automation -m "not integration" ./tests
