#!/bin/sh

if [ ! -f "./app/backend/.env" ]; then
    echo ""
    echo "No app/backend/.env found."
    if command -v azd >/dev/null 2>&1; then
        echo "Attempting to generate it via azd (scripts/write_env.sh)..."
        ./scripts/write_env.sh || true
    else
        echo "azd not found. Create app/backend/.env (or run scripts/write_env.sh after installing azd)."
    fi
fi

echo ""
echo "Restoring frontend npm packages"
echo ""
cd app/frontend
npm install
if [ $? -ne 0 ]; then
    echo "Failed to restore frontend npm packages"
    exit $?
fi

echo ""
echo "Building frontend"
echo ""
npm audit fix
npm run build
if [ $? -ne 0 ]; then
    echo "Failed to build frontend"
    exit $?
fi

echo ""
echo "Starting backend"
echo ""
cd ../../
./.venv/bin/python app/backend/app.py &
if [ $? -ne 0 ]; then
    echo "Failed to start backend"
    exit $?
fi

echo ""
echo "Starting api"
echo ""
./.venv/bin/python app/api/main.py
if [ $? -ne 0 ]; then
    echo "Failed to start api"
    exit $?
fi
