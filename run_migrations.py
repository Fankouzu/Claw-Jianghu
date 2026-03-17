#!/usr/bin/env python
"""
Direct Django migration script that bypasses Evennia's database check.
"""
import os
import sys
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')

# Initialize Django
django.setup()

# Now run migrations
from django.core.management import call_command

print("Running Django migrations...")
try:
    call_command('migrate', verbosity=1)
    print("Migrations completed successfully!")
except Exception as e:
    print(f"Migration error: {e}")
    sys.exit(1)