# ── 后端开发命令 ────────────────────────────────────

.PHONY: install test lint format typecheck clean

install:
	pip install -r requirements.txt -r requirements-test.txt

test:
	python -m pytest --cov=app --cov-report=term-missing -v

test-xml:
	python -m pytest --cov=app --cov-report=xml --cov-report=term-missing -v

lint:
	ruff check app/

lint-fix:
	ruff check app/ --fix

format:
	ruff format app/

format-check:
	ruff format app/ --check

typecheck:
	mypy app/

check: lint format-check typecheck test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
