#!/bin/bash
# Rozwiązanie z SSH tunnel - najprostsze, bez captcha!

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}📱 URUCHAMIANIE Z SSH TUNNEL${NC}"
echo ""
echo -e "${YELLOW}Krok 1: Wpisz hasło SSH (jeśli poprosi)${NC}"
echo ""
echo -e "${BLUE}To uruchomi publiczny URL dla Twojej aplikacji!${NC}"
echo ""

ssh -R 80:localhost:8501 serveo.net

