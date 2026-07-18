.PHONY: setup test etl export up down logs verify clean

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@test -f .env || cp .env.example .env

test:
	PYTHONPATH=. .venv/bin/pytest -v --cov=etl --cov-report=term-missing

# Start PostgreSQL only (for local dev)
db-up:
	docker compose up -d db adminer

# Run full pipeline in Docker (db + etl)
up:
	docker compose up --build

# Run ETL locally (db must be running)
etl:
	PYTHONPATH=. .venv/bin/python -m etl.run_etl

# Export DB tables + analytics views to data/*.csv
export:
	PYTHONPATH=. .venv/bin/python -m etl.export_csv

down:
	docker compose down

logs:
	docker compose logs -f

# Quick health check
verify:
	@bash scripts/verify_setup.sh

clean:
	docker compose down -v
	rm -rf .pytest_cache .coverage
