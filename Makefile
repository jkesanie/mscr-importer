.PHONY: install run harvest ingest validate help dev-format dev-lint dev-test

# Setup
install:
	poetry install

install-dev:
	poetry install --with dev

# Run CLI
run:
	poetry run python mscr_importer.py

# Commands
harvest:
	poetry run python mscr_importer.py harvest $(URL) --api $(MSCR_API_URL) --key $(MSCR_API_KEY)

ingest:
	poetry run python mscr_importer.py ingest $(FILE) --api $(MSCR_API_URL) --key $(MSCR_API_KEY)

validate:
	poetry run python mscr_importer.py validate $(PATH_OR_URL)

# Development tasks
dev-format:
	poetry run black .

dev-lint:
	poetry run ruff check .

dev-test:
	poetry run pytest

dev-test-cov:
	poetry run pytest --cov=.

# Help
help:
	poetry run python mscr_importer.py --help