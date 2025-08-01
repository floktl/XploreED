# 🧪 Testing Infrastructure

This folder contains all testing-related files and configurations.

## 📁 Contents

### **End-to-End Tests**
- **`cypress-tests/`** - Cypress end-to-end testing suite

## 🔧 Usage

### **Running Cypress Tests**
```bash
# From project root
make cytest

# Or manually
cd tests/cypress-tests
npm install
npm run cypress:open
```

### **Test Configuration**
The Cypress tests are configured to test the full application stack:
- Frontend React application
- Backend Flask API
- Database interactions
- User workflows

## 📝 Notes

- Tests run against the full Docker stack
- Requires the application to be running (`make run`)
- Tests are automated in CI/CD pipeline
- Test results are reported in the build process
