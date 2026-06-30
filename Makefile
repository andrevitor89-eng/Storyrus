.PHONY: init up down logs seed demo test-backend test-web e2e

# Copia o .env (uma vez) — preencha as chaves de IA depois.
init:
	cp -n backend/.env.example backend/.env || true
	@echo "Pronto. Edite backend/.env com suas chaves antes de usar o pipeline real."

# Sobe a stack completa (db, redis, api, worker, web).
up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api worker

# Popula o banco com usuário demo (demo@forteshub.com / demo12345).
seed:
	docker compose run --rm api python scripts/seed.py

# Exercita o fluxo ponta a ponta contra a API em execução.
demo:
	docker compose run --rm -e API_URL=http://api:8000 api python scripts/demo_flow.py

test-backend:
	cd backend && pytest -q

test-web:
	cd apps/web && npm run test:run

e2e:
	cd apps/web && npm run e2e
