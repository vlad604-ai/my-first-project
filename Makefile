.PHONY: install migrate seed demo api bot worker web test lint up down

install:
	cd backend && pip install -r requirements.txt
	cd web && npm install

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m scripts.seed

demo:
	cd backend && python -m scripts.seed --demo

api:
	cd backend && uvicorn app.main:app --reload --port 8000

bot:
	cd backend && python -m bot.main

worker:
	cd backend && python -m worker.main

web:
	cd web && npm run dev

test:
	cd backend && python -m pytest -q

lint:
	cd backend && ruff check app bot worker scripts tests --select E,F,W,B --ignore E501,B008,B904,B905
	cd web && npm run typecheck

up:
	docker compose --profile polling up -d --build

down:
	docker compose --profile polling down
