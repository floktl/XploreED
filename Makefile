.PHONY: build run migrate logs stop prune rebuild reset cytest shell

IMAGE_NAME=german_class_tool
CONTAINER_NAME=german_class_tool_dev

# === Build the Docker image (runs DB migration during build) ===
build:
	@echo "📦 Building Docker image (includes DB migration)..."
	@docker build -t $(IMAGE_NAME) .

# === Run the container locally ===
run:
	@echo "🚀 Running container on http://localhost:8080 ..."
	@if [ -z "$$(docker images -q $(IMAGE_NAME))" ]; then \
		echo "📦 Image not found — building first..."; \
		make build; \
	fi
	@docker run -it --rm -d \
		--name $(CONTAINER_NAME) \
		-p 8080:80 \
		--env-file backend/secrets/.env \
		$(IMAGE_NAME)
	@sleep 2
	@docker logs -f $(CONTAINER_NAME)

# === Run DB migration again manually (if needed) ===
migrate:
	@echo "🔁 Re-running DB migration manually..."
	@docker run --rm \
		--env-file backend/secrets/.env \
		$(IMAGE_NAME) \
		python3 backend/utils/setup/migration_script.py

# === Run Cypress tests ===
cytest:
	@echo "🧪 Running Cypress tests..."
	@docker build -t cypress-only ./cypress-tests
	@docker run --rm -it \
		-v $$PWD/cypress-tests:/e2e \
		-w /e2e \
		--network host \
		cypress-only

# === View logs ===
logs:
	@docker logs -f $(CONTAINER_NAME)

# === Stop the container ===
stop:
	@echo "🛑 Stopping container..."
	@docker stop $(CONTAINER_NAME) || true

# === Full rebuild ===
rebuild:
	@echo "🔁 Rebuilding image from scratch..."
	@docker image rm -f $(IMAGE_NAME)
	@make build

# === Clean up Docker data ===
prune:
	@echo "🔥 Pruning Docker system..."
	@docker system prune -af --volumes

# === Full reset ===
reset:
	@make stop
	@make prune
	@make build
	@make run

# === Open shell inside running container ===
shell:
	@docker exec -it $(CONTAINER_NAME) sh
