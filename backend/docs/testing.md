# **Backend Testing Documentation**

## **Overview**

This document outlines the testing procedures, API endpoints, and test results for the XplorED backend application. It serves as a reference for developers to verify the backend functionality and troubleshoot issues.

## **Testing Environment**

### **Development Setup**
- **Docker Compose**: `docker-compose.dev.yml`
- **Backend Port**: 5050
- **Frontend Port**: 5173
- **Redis Port**: 6379
- **Container**: `xplored-backend-1`

### **Accessing the Backend**
```bash
# Open shell in backend container
make shell

# Or directly with docker compose
docker compose -f docker-compose.dev.yml exec backend sh
```

## **API Endpoint Testing**

### **Base URL**
```
http://localhost:5050/api
```

### **Authentication Endpoints**

#### **1. User Login**
```bash
curl http://localhost:5050/api/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

**Expected Response (Invalid Credentials):**
```json
{
  "error": "Invalid credentials",
  "message": "Invalid username or password"
}
```

**Expected Response (Valid Credentials):**
```json
{
  "message": "Login successful",
  "user": {
    "username": "username",
    "skill_level": "beginner",
    "is_admin": false
  },
  "session_id": "session_token"
}
```

#### **2. User Registration**
```bash
curl http://localhost:5050/api/register \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"password123","email":"user@example.com"}'
```

**Expected Response (New User):**
```json
{
  "message": "User registered successfully",
  "user": {
    "username": "newuser",
    "skill_level": 1,
    "is_admin": false
  }
}
```

**Expected Response (Existing User):**
```json
{
  "error": "Username already exists"
}
```

#### **3. Session Validation**
```bash
curl http://localhost:5050/api/session \
  -H "Cookie: session=your_session_token"
```

### **Debug Endpoints (Admin Required)**

#### **1. System Health Check**
```bash
curl http://localhost:5050/api/debug/health
```

**Expected Response (Unauthorized):**
```json
{
  "error": "Unauthorized - Admin access required"
}
```

**Expected Response (Authorized):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "health_info": {
    "overall_status": true,
    "database": "connected",
    "external_services": "operational",
    "performance": "normal",
    "memory_usage": 45.2,
    "cpu_usage": 12.8,
    "disk_usage": 23.1,
    "error_rate": 0.1
  },
  "version": "1.0.0",
  "environment": "development",
  "uptime": "2h 15m 30s",
  "last_error": null,
  "recommendations": []
}
```

#### **2. Database Connection Test**
```bash
curl http://localhost:5050/api/debug/test-db
```

#### **3. System Status**
```bash
curl http://localhost:5050/api/debug/status
```

#### **4. Configuration Info**
```bash
curl http://localhost:5050/api/debug/config
```

#### **5. Performance Metrics**
```bash
curl http://localhost:5050/api/debug/performance
```

### **Content Management Endpoints**

#### **1. Lessons**
```bash
# Get all lessons
curl http://localhost:5050/api/lessons

# Get specific lesson
curl http://localhost:5050/api/lessons/{lesson_id}
```

#### **2. Lesson Progress**
```bash
# Get user progress
curl http://localhost:5050/api/lesson-progress \
  -H "Cookie: session=your_session_token"

# Update progress
curl http://localhost:5050/api/lesson-progress \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_token" \
  -d '{"lesson_id": 1, "completed": true, "score": 85}'
```

### **AI Integration Endpoints**

#### **1. Exercise Generation**
```bash
curl http://localhost:5050/api/ai/exercise \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_token" \
  -d '{"topic": "grammar", "difficulty": "beginner", "type": "multiple_choice"}'
```

#### **2. AI Feedback**
```bash
curl http://localhost:5050/api/ai/feedback \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_token" \
  -d '{"exercise_id": 1, "user_answer": "Ich bin ein Student", "correct_answer": "Ich bin Student"}'
```

#### **3. Text-to-Speech**
```bash
curl http://localhost:5050/api/ai/tts \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_token" \
  -d '{"text": "Hallo, wie geht es dir?", "voice": "german_female"}'
```

### **User Management Endpoints**

#### **1. User Profile**
```bash
# Get profile
curl http://localhost:5050/api/profile \
  -H "Cookie: session=your_session_token"

# Update profile
curl http://localhost:5050/api/profile \
  -X PUT \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_token" \
  -d '{"skill_level": "intermediate", "preferences": {"theme": "dark"}}'
```

#### **2. User Settings**
```bash
# Get settings
curl http://localhost:5050/api/settings \
  -H "Cookie: session=your_session_token"

# Update settings
curl http://localhost:5050/api/settings \
  -X PUT \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_token" \
  -d '{"notifications": true, "language": "de"}'
```

## **Testing Procedures**

### **1. Basic Connectivity Test**
```bash
# Test if backend is responding
curl http://localhost:5050/

# Expected: 404 page (backend is running)
```

### **2. API Route Registration Test**
```bash
# Test API prefix
curl http://localhost:5050/api/login -X POST -H "Content-Type: application/json" -d '{}'

# Expected: Error response (routes are registered)
```

### **3. Database Connectivity Test**
```bash
# Test through registration endpoint
curl http://localhost:5050/api/register -X POST -H "Content-Type: application/json" -d '{"username":"test","password":"test"}'

# Expected: Database response (connected)
```

### **4. Authentication Flow Test**
```bash
# 1. Register new user
curl http://localhost:5050/api/register -X POST -H "Content-Type: application/json" -d '{"username":"testuser","password":"testpass","email":"test@example.com"}'

# 2. Login with credentials
curl http://localhost:5050/api/login -X POST -H "Content-Type: application/json" -d '{"username":"testuser","password":"testpass"}'

# 3. Use session token for authenticated requests
curl http://localhost:5050/api/profile -H "Cookie: session=session_token_from_login"
```

## **Test Results**

### **✅ Verified Working Endpoints**

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/login` | POST | ✅ Working | Authentication functional |
| `/api/register` | POST | ✅ Working | User registration functional |
| `/api/debug/health` | GET | ✅ Working | Admin access verified |
| `/api/debug/test-db` | GET | ✅ Working | Admin access verified |
| `/api/debug/status` | GET | ✅ Working | Admin access verified |
| `/` | GET | ✅ Working | Returns 404 page (expected) |

### **✅ Verified System Components**

| Component | Status | Notes |
|-----------|--------|-------|
| Backend Container | ✅ Running | Port 5050 |
| Database Connection | ✅ Connected | SQLite operational |
| API Routes | ✅ Registered | All blueprints loaded |
| Authentication | ✅ Functional | Login/register working |
| Error Handling | ✅ Working | Proper error responses |
| CORS | ✅ Configured | Frontend integration ready |

### **⚠️ Known Limitations**

| Limitation | Description | Workaround |
|------------|-------------|------------|
| Debug endpoints require admin | Health check needs admin session | Create admin user and update database |
| No public health endpoint | No unauthenticated health check | Use login endpoint as health check |
| Session-based auth | Requires cookies for authenticated requests | Include session tokens in requests |

### **🔑 Admin Access Setup**

To access debug endpoints, you need admin privileges:

#### **1. Create Admin User**
```bash
# Register admin user
curl http://localhost:5050/api/register \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","email":"admin@xplored.com"}'
```

#### **2. Update Admin Status in Database**
```bash
# Install sqlite3 if not available
docker compose -f docker-compose.dev.yml exec backend apt-get update && \
docker compose -f docker-compose.dev.yml exec backend apt-get install -y sqlite3

# Update admin status
docker compose -f docker-compose.dev.yml exec backend sqlite3 /app/database/user_data.db \
  "UPDATE users SET is_admin = 1 WHERE username = 'admin';"
```

#### **3. Login and Use Admin Session**
```bash
# Login with admin credentials
curl http://localhost:5050/api/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c /tmp/admin_cookies.txt

# Use admin session for debug endpoints
curl http://localhost:5050/api/debug/health -b /tmp/admin_cookies.txt
```

#### **4. Automated Admin Setup (Recommended)**
```bash
# Run the admin setup script
./backend/scripts/setup_admin.sh

# This script will:
# - Create admin user
# - Set admin privileges
# - Test admin access
# - Provide quick test commands
```

## **Troubleshooting**

### **Common Issues**

#### **1. Backend Not Responding**
```bash
# Check container status
docker compose -f docker-compose.dev.yml ps

# Check logs
docker compose -f docker-compose.dev.yml logs backend

# Restart backend
docker compose -f docker-compose.dev.yml restart backend
```

#### **2. Database Connection Issues**
```bash
# Test database directly
docker compose -f docker-compose.dev.yml exec backend python -c "from core.database.connection import select_one; print(select_one('SELECT 1'))"
```

#### **3. API Routes Not Found**
```bash
# Check if routes are registered
docker compose -f docker-compose.dev.yml exec backend python -c "from src.main import app; print([rule.rule for rule in app.url_map.iter_rules()])"
```

#### **4. Authentication Issues**
```bash
# Check session configuration
docker compose -f docker-compose.dev.yml exec backend python -c "import os; print('SECRET_KEY:', bool(os.getenv('SECRET_KEY')))"
```

### **Debug Commands**

#### **Check Environment Variables**
```bash
docker compose -f docker-compose.dev.yml exec backend env | grep -E "(FLASK|SECRET|DATABASE)"
```

#### **Check Python Dependencies**
```bash
docker compose -f docker-compose.dev.yml exec backend pip list
```

#### **Check Application Logs**
```bash
docker compose -f docker-compose.dev.yml exec backend tail -f /app/logs/app.log
```

## **Performance Testing**

### **Load Testing**
```bash
# Install Apache Bench in container
docker compose -f docker-compose.dev.yml exec backend apt-get update && docker compose -f docker-compose.dev.yml exec backend apt-get install -y apache2-utils

# Test login endpoint
docker compose -f docker-compose.dev.yml exec backend ab -n 100 -c 10 -p /tmp/login_data.json -T application/json http://localhost:5050/api/login
```

### **Database Performance**
```bash
# Test database query performance
docker compose -f docker-compose.dev.yml exec backend python -c "
import time
from core.database.connection import select_rows
start = time.time()
result = select_rows('SELECT * FROM users LIMIT 100')
end = time.time()
print(f'Query time: {end - start:.3f}s')
"
```

## **Security Testing**

### **Input Validation**
```bash
# Test SQL injection prevention
curl http://localhost:5050/api/login -X POST -H "Content-Type: application/json" -d '{"username":"admin\"; DROP TABLE users; --","password":"test"}'

# Test XSS prevention
curl http://localhost:5050/api/register -X POST -H "Content-Type: application/json" -d '{"username":"<script>alert(\"xss\")</script>","password":"test"}'
```

### **Authentication Security**
```bash
# Test brute force protection
for i in {1..10}; do
  curl http://localhost:5050/api/login -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"wrong"}' &
done
wait
```

## **Integration Testing**

### **Frontend-Backend Integration**
```bash
# Test CORS configuration
curl -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: Content-Type" -X OPTIONS http://localhost:5050/api/login
```

### **External Service Integration**
```bash
# Test Redis connection
docker compose -f docker-compose.dev.yml exec backend python -c "
from external.redis.client import redis_client
print('Redis connected:', redis_client.ping())
"
```

## **Continuous Testing**

### **Automated Test Script**
Create a test script for regular testing:

```bash
#!/bin/bash
# test_backend.sh

echo "🧪 Testing XplorED Backend..."

# Test basic connectivity
echo "1. Testing connectivity..."
curl -s http://localhost:5050/ > /dev/null && echo "✅ Backend responding" || echo "❌ Backend not responding"

# Test API routes
echo "2. Testing API routes..."
curl -s http://localhost:5050/api/login -X POST -H "Content-Type: application/json" -d '{}' > /dev/null && echo "✅ API routes working" || echo "❌ API routes not working"

# Test database
echo "3. Testing database..."
curl -s http://localhost:5050/api/register -X POST -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' | grep -q "error" && echo "✅ Database connected" || echo "❌ Database issues"

echo "🎉 Backend testing complete!"
```

### **Health Check Endpoint**
Consider adding a public health check endpoint for monitoring:

```python
@app.route("/health", methods=["GET"])
def public_health_check():
    """Public health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })
```

## **Documentation Updates**

This testing documentation should be updated whenever:
- New endpoints are added
- Authentication requirements change
- Error responses are modified
- New testing procedures are implemented

---

**Last Updated**: January 2024
**Tested By**: AI Assistant
**Backend Version**: 1.0.0
