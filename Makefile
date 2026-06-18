.PHONY: dev test lint down logs

dev:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up --build -d
	@echo "Waiting for migrations..."
	@sleep 5
	@echo "Service is up at http://localhost:8000"

test:
	cd backend && \
		python3 -m venv .venv && \
		.venv/bin/pip install -q -r requirements.txt aiosqlite && \
		DATABASE_URL=sqlite+aiosqlite:///./test.db \
		REDIS_URL=redis://localhost:6379/0 \
		PYTHONPATH=. \
		.venv/bin/pytest tests/ -v

lint:
	cd backend && python3 -m venv .venv && \
	.venv/bin/pip install -q ruff && .venv/bin/ruff check app/ tests/

down:
	docker compose down -v

logs:
	docker compose logs -f api worker
