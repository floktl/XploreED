#!/bin/bash

# XplorED Backend - Admin Setup Script
# This script creates an admin user and sets up admin access for testing

set -e

echo "🔧 Setting up admin access for XplorED Backend..."

# Configuration
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"
ADMIN_EMAIL="admin@xplored.com"
BACKEND_URL="http://localhost:5050"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if backend is running
echo "1. Checking backend connectivity..."
if curl -s "$BACKEND_URL/" > /dev/null; then
    print_status "Backend is running"
else
    print_error "Backend is not running. Please start the backend first."
    exit 1
fi

# Create admin user
echo "2. Creating admin user..."
REGISTER_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\",\"email\":\"$ADMIN_EMAIL}")

if echo "$REGISTER_RESPONSE" | grep -q "Account created successfully"; then
    print_status "Admin user created successfully"
elif echo "$REGISTER_RESPONSE" | grep -q "Username already exists"; then
    print_status "Admin user already exists"
else
    print_warning "Registration response: $REGISTER_RESPONSE"
    print_warning "Continuing with existing user..."
fi

# Install sqlite3 if not available
echo "3. Installing sqlite3..."
docker compose -f docker-compose.dev.yml exec backend apt-get update > /dev/null 2>&1 || true
docker compose -f docker-compose.dev.yml exec backend apt-get install -y sqlite3 > /dev/null 2>&1 || true

# Update admin status in database
echo "4. Setting admin privileges..."
docker compose -f docker-compose.dev.yml exec backend sqlite3 /app/database/user_data.db \
    "UPDATE users SET is_admin = 1 WHERE username = '$ADMIN_USERNAME';" 2>/dev/null || true

# Wait a moment for the database update to complete
sleep 1

# Verify admin status
ADMIN_STATUS=$(docker compose -f docker-compose.dev.yml exec backend sqlite3 /app/database/user_data.db \
    "SELECT is_admin FROM users WHERE username = '$ADMIN_USERNAME';" 2>/dev/null || echo "0")

if [ "$ADMIN_STATUS" = "1" ]; then
    print_status "Admin privileges already set"
elif [ "$ADMIN_STATUS" = "0" ]; then
    print_warning "User exists but doesn't have admin privileges. Setting them now..."

    # Try to set admin privileges
    docker compose -f docker-compose.dev.yml exec backend sqlite3 /app/database/user_data.db \
        "UPDATE users SET is_admin = 1 WHERE username = '$ADMIN_USERNAME';" 2>/dev/null || true

    # Wait for database update
    sleep 2

    # Verify again
    ADMIN_STATUS=$(docker compose -f docker-compose.dev.yml exec backend sqlite3 /app/database/user_data.db \
        "SELECT is_admin FROM users WHERE username = '$ADMIN_USERNAME';" 2>/dev/null || echo "0")

    if [ "$ADMIN_STATUS" = "1" ]; then
        print_status "Admin privileges set successfully"
    else
        print_warning "Could not set admin privileges. You may need to set them manually."
    fi
else
    print_warning "Could not verify admin privileges. You may need to set them manually."
fi

# Test admin login
echo "5. Testing admin login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\"}" \
    -c /tmp/admin_cookies.txt)

if echo "$LOGIN_RESPONSE" | grep -q "Login successful"; then
    print_status "Admin login successful"
else
    print_error "Admin login failed: $LOGIN_RESPONSE"
    exit 1
fi

# Test admin access to debug endpoints
echo "6. Testing admin access to debug endpoints..."

# Test health endpoint
echo "📊 Health Check Response:"
HEALTH_RESPONSE=$(curl -s -b /tmp/admin_cookies.txt "$BACKEND_URL/api/debug/health")
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"

# Test database endpoint
echo ""
echo "🗄️ Database Test Response:"
DB_RESPONSE=$(curl -s -b /tmp/admin_cookies.txt "$BACKEND_URL/api/debug/test-db")
echo "$DB_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DB_RESPONSE"

# Verify both endpoints
if echo "$HEALTH_RESPONSE" | grep -q "status.*healthy" && echo "$DB_RESPONSE" | grep -q "connection_test.*true"; then
    print_status "Admin access to debug endpoints verified"
else
    print_warning "Could not verify admin access to debug endpoints"
fi

echo ""
echo "🎉 Admin setup complete!"
echo ""
echo "📋 Admin Credentials:"
echo "   Username: $ADMIN_USERNAME"
echo "   Password: $ADMIN_PASSWORD"
echo "   Email: $ADMIN_EMAIL"
echo ""
echo "🔗 Quick Test Commands:"
echo "   # Login and save session"
echo "   curl $BACKEND_URL/api/login -X POST -H \"Content-Type: application/json\" \\"
echo "     -d '{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\"}' \\"
echo "     -c /tmp/admin_cookies.txt"
echo ""
echo "   # Test health endpoint"
echo "   curl $BACKEND_URL/api/debug/health -b /tmp/admin_cookies.txt"
echo ""
echo "   # Test database endpoint"
echo "   curl $BACKEND_URL/api/debug/test-db -b /tmp/admin_cookies.txt"
echo ""
echo "📝 Note: Session cookies are saved to /tmp/admin_cookies.txt"
echo "   Use -b /tmp/admin_cookies.txt for authenticated requests for all please"
