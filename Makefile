.PHONY: build run migrate logs stop prune rebuild reset cytest shell db-delete frontend-backend

IMAGE_NAME=XploreED
COMPOSE=docker compose -f docker-compose.dev.yml
DB_FILE=database/user_data.db

# === Run containers ===
run:
	@echo "🚀 Starting frontend and backend..."
	$(COMPOSE) up

# === Build containers ===
build:
	@echo "🔧 Building images..."
	$(COMPOSE) build

# === Migrate DB inside backend container ===
migrate:
	@echo "🔁 Running DB migration inside container..."
	$(COMPOSE) exec backend python scripts/migration_script.py

# === Delete local SQLite database ===
db-delete:
	@echo "🗑️  Deleting local SQLite database: $(DB_FILE)"
	@rm -f $(DB_FILE)
	@echo "✅ Done. You can now run 'make migrate' to recreate it."

# === Tail logs ===
logs:
	@echo "📜 Showing logs..."
	$(COMPOSE) logs -f

# === Stop all services ===
stop:
	@echo "🛑 Stopping all services..."
	$(COMPOSE) down

# === Clean Docker system ===
prune:
	@echo "🔥 Cleaning Docker system..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	docker system prune -af --volumes

# === Full rebuild ===
rebuild:
	@echo "🔁 Rebuilding from scratch..."
	@make stop
	@docker image rm -f $(IMAGE_NAME) || true
	@make build

# === Full reset (prune + rebuild + run) ===
reset:
	@make stop
	@make prune
	@make db-delete
	@make build
	@make run

# === Run Cypress end-to-end tests ===
cytest:
	@echo "🧪 Running Cypress tests..."
	docker build -t cypress-only ./tests/cypress-tests
	docker run --rm -it \
		-v $$PWD/tests/cypress-tests:/e2e \
		-w /e2e \
		--network host \
		cypress-only

# === Shell into backend container ===
shell:
	@echo "🐚 Opening shell in backend..."
	$(COMPOSE) exec backend sh

# === Start only frontend and backend ===
frontend-backend:
	@echo "🌐 Starting only frontend and backend..."
	$(COMPOSE) up frontend backend
