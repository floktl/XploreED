# --- Stage 1: Build frontend ---
FROM node:20 AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

    # --- Stage 2: Backend dependencies + app copy ---
    FROM python:3.11-slim AS backend
    WORKDIR /app/backend
    COPY backend/requirements.txt .
    RUN pip install --break-system-packages -r requirements.txt
    COPY backend/ .

    # --- Stage 3: Final container with Python + Nginx ---
    FROM python:3.11-slim

    # Install system packages
    RUN apt update && \
        apt install -y nginx sqlite3 && \
        rm -rf /var/lib/apt/lists/*

    # Set working directory
    WORKDIR /app

    # Copy app and frontend
    COPY --from=backend /app/backend /app/backend
        # Create the database directory (if SQLite wants to create the DB)
    RUN mkdir -p /app/database

    COPY --from=frontend /app/frontend/dist /app/frontend/dist
    RUN rm -f /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default
    COPY nginx/default.conf /etc/nginx/conf.d/default.conf


    # Set Python path so "from game" works
    ENV PYTHONPATH=/app/src/backend

    COPY backend/requirements.txt .
    RUN pip install --break-system-packages -r requirements.txt

    # Run database migration script once during image build
    RUN python3 backend/src/app/migration_script.py || true

    # Expose port
    EXPOSE 80
    ENV LC_ALL=C.UTF-8
    ENV LANG=C.UTF-8
    # Start Gunicorn and Nginx
    CMD sh -c "gunicorn --chdir backend/src --bind 0.0.0.0:5050 app:app & nginx -g 'daemon off;'"
