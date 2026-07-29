.PHONY: dev lint test tf-validate

dev:
	docker compose up --build

lint:
	ruff check app
	mypy app

test:
	pytest -q

tf-validate:
	cd infrastructure/environments/dev && terraform init -backend=false && terraform validate

db-init:
	python scripts/initialize_database.py

ingest:
	python scripts/ingest_documents.py

evals:
	python scripts/run_evaluations.py
