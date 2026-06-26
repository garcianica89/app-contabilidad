#!/bin/bash
# Iniciar App Contabilidad en modo desarrollo
# Requiere: Python 3.11+, Node.js 20+, PostgreSQL

echo "=== App Contabilidad - Modo Desarrollo ==="
echo ""

# 1. Verificar backend
cd backend
if [ ! -d "venv" ]; then
    echo "[1/4] Creando entorno virtual Python..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

echo "[2/4] Iniciando backend (FastAPI)..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 2. Verificar frontend
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "[3/4] Instalando dependencias frontend..."
    npm install
fi

echo "[4/4] Iniciando frontend (Vite)..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== Aplicacion iniciada ==="
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Presione Ctrl+C para detener"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
