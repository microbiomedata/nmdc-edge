
test:
	poetry run pytest -m "not integration" --cov-report term-missing --cov=nmdc_automation ./tests
