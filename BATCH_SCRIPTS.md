# Kanrawee Batch Scripts

This folder contains Windows batch scripts for easy development and testing of the Kanrawee project.

## 🚀 Available Scripts

### 1. `setup.bat` - Initial Project Setup
**Run this first when setting up the project**
- ✅ Checks Python and pip installation
- 🏗️ Creates virtual environment
- 📦 Installs all dependencies from requirements.txt
- 🔑 Creates .env template file
- 🔍 Validates project structure

**Usage:**
```bash
setup.bat
```

### 2. `run_dev.bat` - Development Server
**Start the Flask development server**
- 🔧 Activates virtual environment
- 📦 Installs/updates dependencies
- 🔑 Checks for .env file
- 🌟 Starts Flask server on http://127.0.0.1:5000
- 📍 Shows server URLs and status

**Usage:**
```bash
run_dev.bat
```

### 3. `test_system.bat` - System Testing
**Run comprehensive system tests**
- 🔍 Tests MongoDB connection
- 🤖 Tests Gemini AI API
- 🌐 Tests Flask application endpoints
- 📁 Validates important files
- 📊 Shows testing summary

**Usage:**
```bash
test_system.bat
```

### 4. `db_manager.bat` - Database Management
**Interactive database management tool**
- 📊 View MongoDB status
- 👥 View users in database
- 📈 View emotion history statistics
- 🗑️ Clear all data (with confirmation)
- 💾 Export data to JSON backup
- 🔍 Test database connection

**Usage:**
```bash
db_manager.bat
```

## 📋 Recommended Workflow

### First Time Setup:
1. Run `setup.bat` to initialize the project
2. Edit `.env` file with your API keys
3. Run `test_system.bat` to verify setup
4. Run `run_dev.bat` to start development

### Daily Development:
1. Run `run_dev.bat` to start the server
2. Use `test_system.bat` to run tests when needed
3. Use `db_manager.bat` to manage database when needed

## ⚙️ Configuration Requirements

Make sure your `.env` file contains:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here
MONGODB_URI=your_mongodb_connection_string_here

# Optional
SECRET_KEY=your_secret_key_here
```

## 🆘 Troubleshooting

### Common Issues:

**❌ "Python not found"**
- Install Python 3.7+ from https://www.python.org/downloads/
- Make sure Python is added to PATH during installation

**❌ "Virtual environment creation failed"**
- Ensure you have write permissions in the project directory
- Try running as administrator

**❌ "MongoDB connection failed"**
- Check your `MONGODB_URI` in `.env` file
- Ensure MongoDB Atlas cluster is running
- Verify network connectivity

**❌ "Gemini API test failed"**
- Verify your `GEMINI_API_KEY` in `.env` file
- Check API key validity at https://makersuite.google.com/

## 🔧 Script Features

### Automatic Environment Management
- Scripts automatically handle virtual environment activation
- Dependency installation and updates
- Environment variable validation

### Error Handling
- Clear error messages with solutions
- Graceful fallback options
- User-friendly confirmations for dangerous operations

### Visual Interface
- Colorful emoji indicators
- Progress indicators
- Clear section headers
- Helpful status messages

## 📝 Notes

- All scripts are designed for Windows environments
- Scripts assume the project structure follows Kanrawee conventions
- Database operations require valid MongoDB connection
- Testing scripts can run independently of the main server

---

**💡 Tip:** Keep these scripts in your project root directory and run them from Command Prompt or PowerShell for the best experience.
