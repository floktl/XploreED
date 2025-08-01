# 🏗️ Infrastructure

This folder contains infrastructure configuration files for deployment and hosting.

## 📁 Contents

### **Web Server Configuration**
- **`nginx/`** - Nginx web server configuration files

## 🔧 Usage

### **Nginx Configuration**
The `nginx/` folder contains:
- **`default.conf`** - Main Nginx server configuration
- Reverse proxy settings for the application
- SSL/TLS configuration templates
- Static file serving configuration

### **Deployment**
These configurations are used in:
- **Docker containers** - Nginx serves the frontend and proxies to backend
- **Production deployment** - Standalone Nginx server configuration
- **Development environment** - Local Nginx setup

## 📝 Notes

- Configuration files are referenced in Dockerfile and docker-compose
- SSL certificates should be placed in `infra/ssl/` for production
- Configuration supports both HTTP and HTTPS
- Reverse proxy routes API calls to Flask backend
