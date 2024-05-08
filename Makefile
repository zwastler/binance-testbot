format: ## Format code
	ruff format src

test:			## Run tests. For run as "-k test_name" provide test_name (make test [test_name] => pytest -k test_name)
	pytest --disable-warnings --cov src --cov-report=xml --junitxml=report.xml
	coverage report

types:			## Run only types checks
	mypy src

check:			## Run checks (tests, style, types)
	make test
	make format
	make types

uv:			## Install uv (like pip tools).
	pip install -U uv

reqs: 	## Create requirements and sync it.
	rm -f requirements.txt requirements-dev.txt || true
	uv pip compile --generate-hashes requirements.in -o requirements.txt
	uv pip compile --generate-hashes requirements-dev.in -o requirements-dev.txt
	uv pip sync requirements-dev.txt

build:
	docker buildx build -t test_bot_binance -f deployment/Dockerfile .

pre-commit:		## Install pre-commit hooks.
	pre-commit install -t pre-commit -t commit-msg

help:			## Show this help.
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)
