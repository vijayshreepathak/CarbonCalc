.PHONY: up down logs reset

up:
	cd infra && docker compose up --build

down:
	cd infra && docker compose down -v

logs:
	cd infra && docker compose logs -f --tail=200

