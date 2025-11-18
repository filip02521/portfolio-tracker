#!/bin/bash

# Kolorowy output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Uruchamianie Portfolio Tracker dla telefonu...${NC}"
echo ""

# Sprawdź czy ngrok jest zainstalowany
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok nie jest zainstalowany!"
    echo "Zainstaluj: brew install ngrok"
    exit 1
fi

# Zmień na katalog projektu
cd /Users/Filip/portfolio-tracker

# Aktywuj virtual environment
source .venv/bin/activate

echo -e "${GREEN}📱 Wystartowałem Streamlit na http://localhost:8501${NC}"
echo ""
echo "🔍 Ngrok uruchomi się osobno - skopiuj publiczny URL do telefonu"
echo ""
echo "Aby uruchomić Ngrok, otwórz nowy terminal i wpisz:"
echo -e "${BLUE}ngrok http 8501${NC}"
echo ""
echo "Następnie skopiuj HTTPS URL (np. https://abc123.ngrok.io) do telefonu"
echo ""

# Uruchom Streamlit
streamlit run streamlit_app.py

