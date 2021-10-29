.DEFAULT_GOAL := all
isort = isort dspback tests
black = black -S -l 120 --target-version py38 dspback tests

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: install
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

.PHONY: test
test:
	pytest tests

.PHONY: test-cov
test-cov:
	pytest --cov=dspback --cov-report html
