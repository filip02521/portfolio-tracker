#!/bin/bash
# Quick script to check if FINNHUB_API_KEY is set

echo "Checking environment setup..."
echo ""

if [ -f .env ]; then
    echo "✅ .env file found"
    if grep -q "FINNHUB_API_KEY" .env; then
        echo "✅ FINNHUB_API_KEY found in .env"
        # Show first 10 chars and last 4 chars (masked)
        KEY=$(grep "FINNHUB_API_KEY" .env | cut -d'=' -f2 | tr -d ' "')
        if [ ! -z "$KEY" ]; then
            echo "   Key: ${KEY:0:10}...${KEY: -4}"
        else
            echo "   ⚠️  Key is empty!"
        fi
    else
        echo "❌ FINNHUB_API_KEY not found in .env"
        echo "   Add: FINNHUB_API_KEY=your_key_here"
    fi
else
    echo "⚠️  .env file not found"
    echo "   Create .env file in backend directory"
fi

echo ""
if [ ! -z "$FINNHUB_API_KEY" ]; then
    echo "✅ FINNHUB_API_KEY environment variable is set"
    echo "   Key: ${FINNHUB_API_KEY:0:10}...${FINNHUB_API_KEY: -4}"
else
    echo "⚠️  FINNHUB_API_KEY environment variable not set"
fi

echo ""
echo "To set API key:"
echo "1. Add to .env file: FINNHUB_API_KEY=your_key"
echo "2. Or export: export FINNHUB_API_KEY='your_key'"

