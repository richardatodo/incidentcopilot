.PHONY: backend frontend test build up down

backend:
	uvicorn backend.app.main:app --reload

frontend:
	cd frontend && npm run dev

test:
	pytest

build:
	cd frontend && npm run build

up:
	docker compose up --build

down:
	docker compose down
