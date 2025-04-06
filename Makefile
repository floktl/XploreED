.PHONY: up cytest clean stop

up:
	@./scripts/dev-up.sh || true

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



# Prune unused Docker resources
prune:
	docker system prune -f --volumes

# Rebuild everything
rebuild:
	docker-compose down --volumes --remove-orphans
	docker-compose build --no-cache

# View logs from all services
logs:
	docker-compose logs -f --tail=100
