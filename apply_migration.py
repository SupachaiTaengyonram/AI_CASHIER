#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/Users/supachaitaengyonram/Project01')
django.setup()

from django.core.management import call_command

print("Applying migrations...")
call_command('migrate', 'aicashier', verbosity=2)
print("✓ Migration applied successfully")
