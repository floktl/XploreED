# **Deployment Guide**

## **Overview**

This guide covers the deployment of the XplorED backend across different environments, from local development to production. The application is designed to be containerized and can be deployed using Docker and Docker Compose.

## **Prerequisites**

### **System Requirements**
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Python**: Version 3.9 or higher (for local development)
- **Git**: Version control system

### **External Services**
- **Mistral AI API**: For AI-powered features
- **Redis**: For caching and session storage (optional)
- **Database**: SQLite (default) or PostgreSQL (production)

## **Environment Configuration**

### **Environment Variables**

Create a `.env` file in the `backend/secrets/` directory:

```bash
# Database Configuration
DB_FILE=database/user_data.db
DATABASE_URL=sqlite:///database/user_data.db

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here

# AI Services
MISTRAL_API_KEY=your-mistral-api-key
MISTRAL_MODEL=mistral-large-latest

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# Application Settings
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# Security
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### **Environment-specific Configurations**

#### **Development Environment**
```bash
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000
```

#### **Staging Environment**
```bash
FLASK_ENV=staging
FLASK_DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=https://staging.yourdomain.com
```

#### **Production Environment**
```bash
FLASK_ENV=production
FLASK_DEBUG=False
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
```

## **Local Development Deployment**

### **1. Clone and Setup**

```bash
# Clone the repository
git clone <repository-url>
cd XploreED

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements/requirements.txt
```

### **2. Environment Setup**

```bash
# Create secrets directory
mkdir -p backend/secrets

# Create environment file
cp backend/secrets/.env.example backend/secrets/.env

# Edit environment variables
nano backend/secrets/.env
```

### **3. Database Setup**

```bash
# Run database migrations
cd backend
python scripts/migration_script.py
```

### **4. Start Development Server**

```bash
# Start the Flask development server
cd backend
python src/main.py
```

The application will be available at `http://localhost:5000`

## **Docker Deployment**

### **1. Docker Compose Setup**

The project includes a `docker-compose.dev.yml` file for development:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    volumes:
      - ./backend:/app
      - ./backend/database:/app/database
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=True
    env_file:
      - ./backend/secrets/.env
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### **2. Build and Run**

```bash
# Build and start services
docker-compose -f docker-compose.dev.yml up --build

# Run in background
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### **3. Production Docker Compose**

Create `docker-compose.prod.yml` for production:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
    env_file:
      - ./backend/secrets/.env
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/debug/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/default.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  redis_data:
```

## **Production Deployment**

### **1. Server Preparation**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/XploreED
sudo chown $USER:$USER /opt/XploreED
```

### **2. Application Deployment**

```bash
# Clone repository
cd /opt/XploreED
git clone <repository-url> .

# Create environment file
cp backend/secrets/.env.example backend/secrets/.env
nano backend/secrets/.env

# Set proper permissions
chmod 600 backend/secrets/.env

# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build
```

### **3. SSL Certificate Setup**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **4. Nginx Configuration**

Create `infra/nginx/default.conf`:

```nginx
upstream backend {
    server backend:5000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://backend/api/debug/health;
        access_log off;
    }
}
```

## **Cloud Deployment**

### **AWS Deployment**

#### **EC2 Deployment**
```bash
# Launch EC2 instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx

# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Follow server preparation steps above
```

#### **ECS Deployment**
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name XploreED

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
    --cluster XploreED \
    --service-name backend \
    --task-definition XploreED:1 \
    --desired-count 2
```

### **Google Cloud Deployment**

#### **Compute Engine**
```bash
# Create instance
gcloud compute instances create XploreED \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud

# Deploy application
gcloud compute scp --recurse ./backend instance-name:/opt/XploreED/
```

#### **Cloud Run**
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/XploreED

# Deploy to Cloud Run
gcloud run deploy XploreED \
    --image gcr.io/PROJECT_ID/XploreED \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

### **Azure Deployment**

#### **App Service**
```bash
# Create resource group
az group create --name XploreED --location eastus

# Create app service plan
az appservice plan create --name XploreED-plan --resource-group XploreED --sku B1

# Create web app
az webapp create --name XploreED --resource-group XploreED --plan XploreED-plan --runtime "PYTHON|3.9"
```

## **Monitoring and Maintenance**

### **1. Health Monitoring**

```bash
# Check application health
curl http://localhost:5000/api/debug/health

# Check database connectivity
curl http://localhost:5000/api/debug/test-db

# Monitor logs
docker-compose logs -f backend
```

### **2. Backup Strategy**

```bash
# Database backup
docker exec -it XploreED-backend-1 sqlite3 database/user_data.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Automated backup script
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker exec XploreED-backend-1 sqlite3 database/user_data.db ".backup $BACKUP_DIR/backup_$DATE.db"
find $BACKUP_DIR -name "backup_*.db" -mtime +7 -delete
```

### **3. Performance Monitoring**

```bash
# Monitor system resources
htop

# Monitor Docker containers
docker stats

# Check application performance
curl http://localhost:5000/api/debug/performance
```

### **4. Log Management**

```bash
# View application logs
docker-compose logs backend

# Follow logs in real-time
docker-compose logs -f backend

# Rotate logs
docker-compose exec backend logrotate /etc/logrotate.conf
```

## **Scaling and High Availability**

### **1. Horizontal Scaling**

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - REDIS_URL=redis://redis:6379
```

### **2. Load Balancer Setup**

```nginx
upstream backend {
    server backend1:5000;
    server backend2:5000;
    server backend3:5000;
}
```

### **3. Database Scaling**

```bash
# PostgreSQL setup for production
docker run -d \
    --name postgres \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=XploreED \
    -v postgres_data:/var/lib/postgresql/data \
    postgres:13
```

## **Security Considerations**

### **1. Network Security**

```bash
# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### **2. Container Security**

```bash
# Run containers as non-root user
docker run --user 1000:1000 XploreED

# Scan for vulnerabilities
docker scan XploreED
```

### **3. Secrets Management**

```bash
# Use Docker secrets
echo "your-secret-key" | docker secret create secret_key -

# Use environment variables
docker run -e SECRET_KEY=your-secret-key XploreED
```

## **Troubleshooting**

### **Common Issues**

#### **Database Connection Errors**
```bash
# Check database file permissions
ls -la backend/database/

# Recreate database
rm backend/database/user_data.db
python scripts/migration_script.py
```

#### **Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep :5000

# Change port in docker-compose.yml
ports:
  - "5001:5000"
```

#### **Memory Issues**
```bash
# Monitor memory usage
docker stats

# Increase memory limits
docker run --memory=2g XploreED
```

### **Debug Commands**

```bash
# Enter container shell
docker-compose exec backend bash

# Check environment variables
docker-compose exec backend env

# View application logs
docker-compose logs backend

# Restart services
docker-compose restart backend
```

## **Rollback Procedures**

### **1. Application Rollback**

```bash
# Revert to previous version
git checkout HEAD~1

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### **2. Database Rollback**

```bash
# Restore from backup
docker exec -it backend sqlite3 database/user_data.db ".restore backup_20240101_120000.db"
```

---

This deployment guide provides comprehensive instructions for deploying the XplorED backend across various environments and platforms. Follow the appropriate section based on your deployment target and requirements.
