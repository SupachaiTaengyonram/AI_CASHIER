#!/bin/bash
# Run Django development server for AI CASHIER

cd /Users/supachaitaengyonram/Project01

echo "🚀 Starting AI CASHIER Django Server..."
echo "📍 URL: http://127.0.0.1:8000/"
echo "📊 Overview: http://127.0.0.1:8000/overviews/"
echo "⚠️  Press Ctrl+C to stop server"
echo ""

/Users/supachaitaengyonram/Project01/.env06/bin/python manage.py runserver
