@echo off
REM Local development setup script for Windows

echo Setting up Adaptive Ad Intelligence Platform for local development

REM Check Python version
python --version

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your configuration
) else (
    echo .env file already exists
)

REM Create necessary directories
echo Creating directory structure...
if not exist "src\agents" mkdir src\agents
if not exist "src\models" mkdir src\models
if not exist "src\services" mkdir src\services
if not exist "src\api" mkdir src\api
if not exist "tests" mkdir tests
if not exist "logs" mkdir logs

REM Create __init__.py files
type nul > src\agents\__init__.py
type nul > src\models\__init__.py
type nul > src\services\__init__.py
type nul > src\api\__init__.py
type nul > tests\__init__.py

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your Google Cloud configuration
echo 2. Set GOOGLE_APPLICATION_CREDENTIALS to your service account key path
echo 3. Run: venv\Scripts\activate.bat
echo 4. Run: python -m src.main
echo.
echo The API will be available at http://localhost:8080
echo API documentation: http://localhost:8080/docs

pause
