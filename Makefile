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

.PHONY: test-cov-gh-action
test-cov-gh-action:
	docker exec dsp_dev_dspback pytest tests --cov=dspback --cache-clear > pytest-coverage.txt

.PHONY: default-env
default-env:
	wget -N https://raw.githubusercontent.com/cznethub/dsp/develop/.env

.PHONY: up
up:
	docker-compose --env-file .env up dspback

.PHONY: up-d
up-d:
	docker-compose --env-file .env up -d dspback

.PHONY: up-all
up-all:
	docker-compose --env-file .env up

.PHONY: up-all-d
up-all-d:
	docker-compose --env-file .env up -d

.PHONY: down
down:
	docker-compose --env-file .env down

.PHONY: build
build:
	docker-compose --env-file .env build dspback

.PHONY: build-all
build-all:
	docker-compose --env-file .env build

.PHONY: build-dspfront
build-dspfront:
	rm -rf dspfront
	git clone https://github.com/cznethub/dspfront.git
	docker build -t dspfront dspfront
	rm -rf dspfront

.PHONY: bash
bash:
	docker exec -it dsp_dev_dspback /bin/bash

.PHONY: build-pydantic-schemas
build-pydantic-schemas:
	docker exec dsp_dev_dspback datamodel-codegen --input-file-type jsonschema --input dspback/schemas/zenodo/schema.json --output dspback/schemas/zenodo/model.py
	docker exec dsp_dev_dspback datamodel-codegen --input-file-type jsonschema --input dspback/schemas/external/schema.json --output dspback/schemas/external/model.py
	docker exec dsp_dev_dspback datamodel-codegen --input-file-type jsonschema --input dspback/schemas/earthchem/schema.json --output dspback/schemas/earthchem/model.py
	docker exec dsp_dev_dspback datamodel-codegen --input-file-type jsonschema --input dspback/schemas/hydroshare/schema.json --output dspback/schemas/hydroshare/model.py
