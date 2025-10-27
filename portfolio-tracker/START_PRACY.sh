#!/bin/bash
# Uruchom aplikację dla pracy - z Ngrok

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📱 STARTUJĘ APLIKACJĘ DLA PRACY${NC}"
echo ""

cd /Users/Filip/portfolio-tracker

# Aktywuj virtual environment
source .venv/bin/activate

# Uruchom Streamlit w tle
echo -e "${BLUE}🚀 Uruchamiam Streamlit...${NC}"
streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501 &

# Czekaj 3 sekundy na start
sleep 3

echo ""
echo -e "${GREEN}✅ Streamlit działa na http://localhost:8501${NC}"
echo ""
echo -e "${YELLOW}📲 TERAZ URUCHOM NGROK:${NC}"
echo -e "${BLUE}W nowym terminalu wpisz:${NC}"
echo ""
echo "  ngrok http 8501"
echo ""
echo -e "${GREEN}Następnie skopiuj URL z ngrok (np. https://xxxxx.ngrok.io)"
echo "i otwórz go na telefonie w pracy!${NC}"
echo ""
echo -e "${YELLOW}⚠️  Aby zatrzymać aplikację, naciśnij Ctrl+C${NC}"

