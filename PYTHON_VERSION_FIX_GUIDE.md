# Python Version Fix Guide - Multilingual Mandi Backend

**Issue**: SQLAlchemy 2.0.46 is incompatible with Python 3.13.7  
**Solution**: Downgrade to Python 3.11 or 3.12  
**Time Required**: 10-15 minutes

---

## Quick Fix Options

### Option 1: Using Python Installer (Recommended for Windows)

1. **Download Python 3.11.7**
   - Visit: https://www.python.org/downloads/release/python-3117/
   - Download: "Windows installer (64-bit)"

2. **Install Python 3.11.7**
   ```cmd
   # Run the installer
   # ✅ Check "Add Python 3.11 to PATH"
   # ✅ Choose "Customize installation"
   # ✅ Install for all users (optional)
   ```

3. **Verify Installation**
   ```cmd
   py -3.11 --version
   # Should show: Python 3.11.7
   ```

4. **Update Backend to Use Python 3.11**
   ```cmd
   cd backend
   
   # Remove old virtual environment
   rmdir /s /q venv
   
   # Create new venv with Python 3.11
   py -3.11 -m venv venv
   
   # Activate
   venv\Scripts\activate
   
   # Verify
   python --version
   # Should show: Python 3.11.7
   
   # Install dependencies
   pip install -r requirements.txt
   ```

---

### Option 2: Using pyenv (For Advanced Users)

**Install pyenv-win**:
```powershell
# Install pyenv-win
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"

# Restart PowerShell, then:
pyenv install 3.11.7
pyenv local 3.11.7
python --version
```

---

### Option 3: Using Conda/Miniconda

```cmd
# Create new environment with Python 3.11
conda create -n multilingual-mandi python=3.11
conda activate multilingual-mandi

cd backend
pip install -r requirements.txt
```

---

## Step-by-Step: Recommended Approach

### Step 1: Check Current Python Version
```cmd
python --version
# Output: Python 3.13.7 (PROBLEM)
```

### Step 2: Install Python 3.11.7

**Windows**:
1. Download from https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
2. Run installer
3. Check "Add Python 3.11 to PATH"
4. Complete installation

**Linux/Ubuntu**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**macOS**:
```bash
brew install python@3.11
```

### Step 3: Recreate Virtual Environment

```cmd
cd backend

# Backup old venv (optional)
move venv venv_old

# Create new venv with Python 3.11
py -3.11 -m venv venv

# OR on Linux/Mac:
# python3.11 -m venv venv

# Activate
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Verify Python version
python --version
# Should show: Python 3.11.7 ✅
```

### Step 4: Install Dependencies

```cmd
# Make sure venv is activated
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Verify Installation

```cmd
# Check SQLAlchemy
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
# Should show: 2.0.46

# Check Python version
python -c "import sys; print(sys.version)"
# Should show: 3.11.7
```

### Step 6: Run Tests

```cmd
# Run a simple test
pytest tests/test_demo_data_provider.py -v

# If successful, run all tests
pytest tests/ -v
```

---

## Troubleshooting

### Issue: "py -3.11" not found

**Solution**: Python 3.11 not installed or not in PATH
```cmd
# Find Python installations
py --list

# If 3.11 not listed, reinstall Python 3.11
```

### Issue: "pip install" fails

**Solution**: Upgrade pip first
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: SQLAlchemy still shows errors

**Solution**: Ensure you're using the correct Python version
```cmd
# Check Python version in venv
python --version

# If still 3.13, deactivate and recreate venv
deactivate
rmdir /s /q venv
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: Import errors after reinstall

**Solution**: Clear Python cache
```cmd
# Remove __pycache__ directories
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"

# Remove .pyc files
del /s /q *.pyc
```

---

## Verification Checklist

After completing the fix, verify:

- [ ] Python version is 3.11.x or 3.12.x
  ```cmd
  python --version
  ```

- [ ] Virtual environment is activated
  ```cmd
  # Should see (venv) in prompt
  ```

- [ ] SQLAlchemy imports without errors
  ```cmd
  python -c "from sqlalchemy import create_engine; print('OK')"
  ```

- [ ] All dependencies installed
  ```cmd
  pip list | findstr sqlalchemy
  ```

- [ ] Tests can be collected
  ```cmd
  pytest --collect-only
  ```

- [ ] At least one test passes
  ```cmd
  pytest tests/test_demo_data_provider.py -v
  ```

---

## Quick Commands Reference

```cmd
# Check Python version
python --version

# List available Python versions (Windows)
py --list

# Create venv with specific Python version
py -3.11 -m venv venv

# Activate venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Deactivate venv
deactivate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_demo_data_provider.py -v
```

---

## After Fix: Run Full Test Suite

```cmd
cd backend
venv\Scripts\activate

# Run all tests
pytest tests/ -v --tb=short

# Expected: All tests should pass
# If any fail, check the error messages
```

---

## Alternative: Use Docker (No Python Install Needed)

If you prefer not to manage Python versions:

```dockerfile
# Create Dockerfile in backend/
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["pytest", "tests/", "-v"]
```

```cmd
# Build and run
docker build -t multilingual-mandi-backend .
docker run multilingual-mandi-backend
```

---

## Need Help?

If you encounter issues:

1. Check Python version: `python --version`
2. Check if venv is activated: Look for `(venv)` in prompt
3. Try recreating venv from scratch
4. Ensure you're using Python 3.11 or 3.12 (NOT 3.13)

---

**Next Steps After Fix**:
1. Run backend tests: `pytest tests/ -v`
2. Verify all tests pass
3. Update PRODUCTION_READY_SUMMARY.md
4. Deploy to production

---

**Document Version**: 1.0.0  
**Last Updated**: January 28, 2026
