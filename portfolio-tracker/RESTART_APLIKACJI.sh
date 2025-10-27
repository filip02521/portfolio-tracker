#!/bin/bash
# Skrypt do restartu aplikacji z czyszczeniem cache

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 RESTART APLIKACJI${NC}"
echo ""

# Zatrzymaj Streamlit
echo "Zatrzymywanie Streamlit..."
pkill -f streamlit
sleep 2

# Usuń cache
echo "Czyszczenie cache..."
rm -rf ~/.streamlit/cache
echo "✅ Cache usunięte"

# Uruchom ponownie
cd /Users/Filip/portfolio-tracker
source .venv/bin/activate

echo ""
echo -e "${GREEN}🚀 Uruchamiam Streamlit ponownie...${NC}"
streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501

