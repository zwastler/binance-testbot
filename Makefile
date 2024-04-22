format: ## Format code
	ruff format src

test:			## Run tests. For run as "-k test_name" provide test_name (make test [test_name] => pytest -k test_name)
	pytest --disable-warnings --cov src --cov-report=xml --junitxml=report.xml -vvvvs
	coverage report


types:			## Run only types checks
	mypy src

check:			## Run checks (tests, style, types)
	#make test
	make format
	make types

uv:			## Install uv (like pip tools).
	pip install -U uv

requirements: uv	## Create requirements.txt from requirements.in for all projects.
	rm -f api/requirements.txt requirements.txt || true
	uv pip compile --generate-hashes requirements.in
	uv pip compile --generate-hashes requirements.in -o requirements.txt

requirements-dev: uv	## Create requirements-dev.txt and sync it.
	uv pip compile --generate-hashes requirements-dev.in -o requirements-dev.txt
	uv pip sync requirements-dev.txt

pre-commit:		## Install pre-commit hooks.
	pre-commit install -t pre-commit -t commit-msg

help:			## Show this help.
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)
