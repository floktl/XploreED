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
COPY backend/requirements/requirements.txt .
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

# Copy backend from backend stage
COPY --from=backend /app/backend /app/backend

# Create the database directory
RUN mkdir -p /app/database

# Copy frontend from frontend stage
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Configure nginx
RUN rm -f /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default
COPY infra/nginx/default.conf /etc/nginx/conf.d/default.conf

# Set Python path for imports
ENV PYTHONPATH=/app/backend/src

# Install Python requirements
COPY backend/requirements/requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

# Debug: Check what files are in the backend directory
RUN echo "=== Backend directory contents ===" && ls -la /app/backend/
RUN echo "=== Scripts directory contents ===" && ls -la /app/backend/scripts/ || echo "Scripts directory not found"

# Run database migration script during build (optional - will run again at startup)
RUN cd /app/backend && DB_FILE=/app/database/user_data.db python3 scripts/migration_script.py || echo "Migration script will run at startup"

# Expose port
EXPOSE 80
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Start Gunicorn and Nginx
CMD sh -c "cd /app/backend && DB_FILE=/app/database/user_data.db python3 scripts/migration_script.py && gunicorn --chdir /app/backend/src --bind 0.0.0.0:5050 main:app & nginx -g 'daemon off;'"
