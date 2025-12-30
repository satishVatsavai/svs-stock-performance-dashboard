#!/bin/bash

# Quick start script for Telegram Portfolio Notifier

echo "🤖 Portfolio Telegram Notifier - Quick Start"
echo "==========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  Please edit .env and add your:"
    echo "   - TELEGRAM_BOT_TOKEN (from @BotFather)"
    echo "   - TELEGRAM_CHAT_ID (from @userinfobot)"
    echo ""
    echo "📚 See TELEGRAM_SETUP.md for detailed instructions"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import telegram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Dependencies not installed"
    echo "Installing required packages..."
    pip3 install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies OK"
fi

echo ""
echo "🚀 Starting Telegram Notifier..."
echo "📅 Notifications will be sent at the scheduled times"
echo "💡 Press Ctrl+C to stop"
echo ""

# Run the notifier
python3 telegram_notifier.py
