# Development Fast Login

This feature provides automatic login functionality for development mode, making it easier to test the application without manually entering credentials.

## Features

### Backend Auto-Login
- **Automatic User Creation**: Creates/updates test user `tester1234` with level 3
- **Session Management**: Automatically creates and manages sessions
- **Middleware**: Sets session cookies for all requests in development mode
- **Development Only**: Only runs when `FLASK_ENV=development`
- **Secure Authentication**: Uses proper password hashing with `generate_password_hash`

### Frontend Fast Login Button
- **Development Only**: Only visible when `import.meta.env.DEV` is true
- **One-Click Login**: Automatically logs in as test user
- **Visual Feedback**: Shows loading state and success/error messages
- **Prominent Styling**: Clearly marked as development feature
- **Skip Onboarding**: Goes directly to main menu, bypassing level selection

## Environment Variables

Add these to your `.env` file:

```bash
TEST_USER=tester1234
TEST_PWD=thisisatest
```

## How It Works

### Backend (Automatic)
1. **Startup**: When backend starts in development mode, it automatically:
   - Creates/updates test user with level 3
   - Creates a session for the test user
   - Logs the session ID

2. **Request Middleware**: For every request:
   - Checks if session cookie exists
   - If not, automatically sets session cookie
   - User is logged in without manual authentication

### Frontend (Manual)
1. **Login Page**: Visit the login page in development mode
2. **Dev Button**: Click the "🚀 Dev Fast Login (tester1234)" button
3. **Auto Login**: Automatically logs in and redirects to the app

## Files Modified

### Backend
- `backend/src/core/development_auto_login.py` - Auto-login logic
- `backend/src/api/middleware/dev_auto_login.py` - Request middleware
- `backend/src/main.py` - Integration and startup

### Frontend
- `frontend/src/components/NameInput.jsx` - Fast login button and logic

## Usage

### For Developers
1. Start the development environment: `docker compose -f docker-compose.dev.yml up`
2. Visit `http://localhost:5173`
3. Click the "🚀 Dev Fast Login" button
4. You're automatically logged in as `tester1234` with level 3 and taken directly to the main menu

### For Testing
- No manual login required
- Consistent test user with known credentials
- Level 3 access for testing all features
- Session automatically managed
- Skips onboarding flow (level selection, placement test)

## Security Notes

- **Development Only**: This feature only works in development mode
- **Proper Password Hashing**: Uses `generate_password_hash` for secure password storage
- **No Production Impact**: Zero impact on production environment
- **Session Management**: Sessions are properly managed and cleaned up

## Troubleshooting

### Backend Issues
- Check logs: `docker compose -f docker-compose.dev.yml logs backend`
- Verify environment variables are set
- Ensure `FLASK_ENV=development`

### Frontend Issues
- Check browser console for errors
- Verify `import.meta.env.DEV` is true
- Ensure backend is running and accessible

### Login Issues
- Check if test user exists in database
- Verify session cookies are being set
- Check API endpoints are responding correctly
