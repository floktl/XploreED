.PHONY: up cytest clean stop prune rebuild logs migrate reset

up:
	@echo "⚙️ Running DB migration inside backend container..."
	@docker compose up -d --wait
	@docker compose exec backend python3 migration_script.py
	@docker compose logs -f


cytest:
	@docker build -t cypress-only ./cypress-tests
	@docker run --rm -it \
		-v $$PWD/cypress-tests:/e2e \
		-w /e2e \
		--network="host" \
		cypress-only

clean:
	@echo "🧹 Cleaning up containers..."
	@docker-compose down --remove-orphans

stop:
	@docker-compose stop

migrate:
	@docker compose exec backend python3 migration_script.py || true

prune:
	docker system prune -f --volumes

rebuild:
	docker-compose down --volumes --remove-orphans
	docker-compose build --no-cache

logs:
	docker-compose logs -f --tail=100

reset:
	@echo "💣 Removing all containers, images, volumes, and networks..."
	@docker-compose down --volumes --remove-orphans
	@docker system prune -af --volumes
	up
