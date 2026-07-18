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
