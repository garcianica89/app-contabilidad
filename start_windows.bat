@echo off
chcp 65001 >nul
title App Contabilidad

echo ========================================
echo      App Contabilidad - Inicio Rapido
echo ========================================
echo.

:: Verificar Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python no encontrado. Instale Python 3.11+ desde python.org
    pause
    exit /b 1
)

:: Verificar Node.js
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js no encontrado. Instale Node.js 20+ desde nodejs.org
    pause
    exit /b 1
)

:: Backend
echo [1/4] Configurando backend...
cd backend
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo [2/4] Iniciando servidor backend...
start "Backend" cmd /c "uvicorn app.main:app --host 127.0.0.1 --port 8000"
cd ..

:: Frontend
echo [3/4] Configurando frontend...
cd frontend
if not exist "node_modules" (
    npm install
)

echo [4/4] Iniciando frontend...
start "Frontend" cmd /c "npm run dev"
cd ..

echo.
echo ========================================
echo  Aplicacion iniciada
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo  Usuario: rgarcia
echo  Clave:   exrgarcia
echo.
echo  Presione cualquier tecla para abrir el navegador
echo  Cierre las ventanas para detener la app
pause >nul

start http://localhost:5173
