#!/bin/bash
# Start backend server using venv Python
cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Check if yfinance is available
python -c "import yfinance; print('✅ yfinance available')" 2>/dev/null || {
    echo "⚠️  yfinance not found in venv. Installing..."
    pip install yfinance==0.2.33
}

# Start backend
echo "Starting backend with venv Python..."
echo "Python: $(which python)"
echo "Port: 8000"
python -m uvicorn main:app --host 0.0.0.0 --port 8000



