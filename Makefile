.PHONY: format lint test clean

format:
	black ui/ worker/ llm/ db/ tests/
	isort ui/ worker/ llm/ db/ tests/

lint:
	flake8 ui/ worker/ llm/ db/ tests/
	mypy ui/ worker/ llm/ db/

test:
	python3 -m pytest tests/ -v

test-unit:
	python3 -m pytest ui/test_*.py worker/test_*.py llm/test_*.py db/test_*.py -v

test-integration:
	python3 -m pytest tests/test_integration.py -v

clean:
	docker system prune -a
	docker volume prune

ci-local:
	./scripts/ci-local.sh

ci-quick:
	./scripts/ci-local.sh --quick
