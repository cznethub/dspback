.DEFAULT_GOAL := all
isort = isort dspback tests
black = black -S -l 120 --target-version py38 dspback tests

.PHONY: format
format:
	docker exec dsp_dev_dspback $(isort)
	docker exec dsp_dev_dspback $(black)

.PHONY: install
install:
	docker exec dsp_dev_dspback pip install -r requirements.txt
	docker exec dsp_dev_dspback pip install -r requirements-dev.txt

.PHONY: test
test:
	docker exec dsp_dev_dspback pytest tests -vv

.PHONY: test-cov
test-cov:
	docker exec dsp_dev_dspback pytest tests --cov=dspback --cov-report html
	docker cp dsp_dev_dspback:htmlcov .

.PHONY: up
up:
	docker-compose --env-file .env up

.PHONY: up-d
up-d:
	docker-compose --env-file .env up -d

.PHONY: down
down:
	docker-compose --env-file .env down

.PHONY: build
build:
	docker-compose --env-file .env build --force-rm

.PHONY: bash
bash:
	docker exec dsp_dev_dspback -it /bin/bash
