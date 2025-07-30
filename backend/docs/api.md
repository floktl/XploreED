# **API Documentation**

## **Overview**

The German Class Tool API is a RESTful service built with Flask that provides comprehensive German language learning functionality. The API follows REST principles and uses JSON for data exchange.

## **Base URL**

```
http://localhost:5000/api
```

## **Authentication**

Most endpoints require authentication via session cookies. Session management is handled automatically by the browser.

### **Session Flow**
1. User registers/logs in via `/api/auth/register` or `/api/auth/login`
2. Server creates a session and returns a session cookie
3. Subsequent requests include the session cookie automatically
4. Session is validated on each protected endpoint

## **Response Format**

All API responses follow a consistent JSON format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message"
}
```

### **Error Responses**

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

## **Core Endpoints**

### **Authentication**

#### **POST /api/auth/register**
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "email": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "username": "string",
    "message": "Registration successful"
  }
}
```

#### **POST /api/auth/login**
Authenticate user and create session.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "username": "string",
    "message": "Login successful"
  }
}
```

#### **POST /api/auth/logout**
Destroy current session.

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### **User Management**

#### **GET /api/user/profile**
Get current user's profile information.

**Response:**
```json
{
  "success": true,
  "data": {
    "username": "string",
    "email": "string",
    "skill_level": 1,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### **PUT /api/user/profile**
Update user profile information.

**Request Body:**
```json
{
  "email": "string (optional)",
  "skill_level": 1 (optional)
}
```

### **Lessons**

#### **GET /api/lessons**
Get available lessons for the current user.

**Response:**
```json
{
  "success": true,
  "data": {
    "lessons": [
      {
        "id": "string",
        "title": "string",
        "description": "string",
        "level": 1,
        "completed": false
      }
    ]
  }
}
```

#### **GET /api/lessons/{lesson_id}**
Get specific lesson content.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "title": "string",
    "content": "string (HTML)",
    "exercises": [...]
  }
}
```

### **Exercises**

#### **POST /api/ai/exercise/generate**
Generate AI-powered exercises.

**Request Body:**
```json
{
  "topic": "string",
  "difficulty": "beginner|intermediate|advanced",
  "exercise_type": "multiple_choice|fill_blank|translation"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "exercise": {
      "id": "string",
      "question": "string",
      "options": ["string"],
      "correct_answer": "string",
      "explanation": "string"
    }
  }
}
```

#### **POST /api/ai/exercise/submit**
Submit exercise answer for evaluation.

**Request Body:**
```json
{
  "exercise_id": "string",
  "answer": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "correct": true,
    "feedback": "string",
    "explanation": "string",
    "score": 85
  }
}
```

### **Vocabulary**

#### **GET /api/vocabulary**
Get user's vocabulary list.

**Response:**
```json
{
  "success": true,
  "data": {
    "vocabulary": [
      {
        "word": "string",
        "translation": "string",
        "repetitions": 0,
        "next_review": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### **POST /api/vocabulary/add**
Add new vocabulary word.

**Request Body:**
```json
{
  "word": "string",
  "translation": "string",
  "context": "string (optional)"
}
```

### **Translation**

#### **POST /api/translate**
Translate text using AI.

**Request Body:**
```json
{
  "text": "string",
  "target_language": "en|de"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "original": "string",
    "translation": "string",
    "confidence": 0.95
  }
}
```

### **Text-to-Speech**

#### **POST /api/ai/tts/generate**
Generate audio for text.

**Request Body:**
```json
{
  "text": "string",
  "voice": "male|female"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "audio_url": "string",
    "duration": 2.5
  }
}
```

## **Admin Endpoints**

### **User Management**

#### **GET /api/admin/users**
Get all users (admin only).

**Response:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "username": "string",
        "email": "string",
        "skill_level": 1,
        "is_admin": false,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### **PUT /api/admin/users/{username}**
Update user (admin only).

**Request Body:**
```json
{
  "skill_level": 2,
  "is_admin": true
}
```

## **Error Codes**

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Authentication required |
| `INVALID_CREDENTIALS` | Invalid username/password |
| `USER_NOT_FOUND` | User does not exist |
| `LESSON_NOT_FOUND` | Lesson does not exist |
| `EXERCISE_NOT_FOUND` | Exercise does not exist |
| `INVALID_INPUT` | Invalid request data |
| `DATABASE_ERROR` | Database operation failed |
| `AI_SERVICE_ERROR` | AI service unavailable |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

## **Rate Limiting**

- **General endpoints**: 100 requests per minute
- **AI endpoints**: 20 requests per minute
- **Authentication endpoints**: 10 requests per minute

## **CORS**

The API supports CORS for frontend integration:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

## **WebSocket Support**

Real-time features are available via WebSocket connections:

```
ws://localhost:5000/ws
```

### **WebSocket Events**

- `exercise_update`: Real-time exercise updates
- `progress_update`: User progress notifications
- `system_notification`: System-wide notifications

## **Testing**

### **Health Check**

```
GET /api/debug/health
```

### **Database Test**

```
GET /api/debug/test-db
```

### **Performance Metrics**

```
GET /api/debug/performance
```

## **Versioning**

API versioning is handled through URL prefixes:

- Current version: `/api/v1/`
- Legacy support: `/api/` (redirects to v1)

## **Deprecation Policy**

- Endpoints are deprecated for 6 months before removal
- Deprecated endpoints return a `Deprecation-Warning` header
- New versions are announced 3 months in advance

---

For more information, see the [Architecture Documentation](architecture.md) and [Deployment Guide](deployment.md).
