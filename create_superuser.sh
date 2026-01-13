#!/bin/bash
# Create a superuser for AI CASHIER admin panel

cd /Users/supachaitaengyonram/Project01

echo "👤 Creating Superuser for AI CASHIER..."
echo ""

/Users/supachaitaengyonram/Project01/.env06/bin/python3 manage.py createsuperuser
