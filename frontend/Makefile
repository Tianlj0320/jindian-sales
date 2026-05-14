# ── 前端开发命令 ────────────────────────────────────

.PHONY: install test test-watch test-coverage test-e2e lint lint-fix format format-check check

install:
	npm install

test:
	npm test

test-watch:
	npm run test:watch

test-coverage:
	npm run test:coverage

test-e2e:
	npx playwright test

lint:
	npm run lint

lint-fix:
	npm run lint:fix

format:
	npm run format

format-check:
	npm run format:check

check: lint format-check test

e2e-install:
	npx playwright install --with-deps chromium
