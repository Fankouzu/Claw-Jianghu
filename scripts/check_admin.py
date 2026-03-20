#!/usr/bin/env python3
"""
Check admin account on Railway.
Run with: railway run python scripts/check_admin.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.railway_ws_settings')

import django
django.setup()

import evennia
evennia._init()

from evennia.accounts.models import AccountDB
from evennia.objects.models import ObjectDB

# Check admin account
admin_account = AccountDB.objects.filter(username="admin").first()
if admin_account:
    print(f"Admin account found: {admin_account}")
    print(f"  Is active: {admin_account.is_active}")
    print(f"  Is staff: {admin_account.is_staff}")
    print(f"  Is superuser: {admin_account.is_superuser}")
    print(f"  DB ID: {admin_account.id}")

    # Check if password can be validated
    from django.contrib.auth import authenticate
    user = authenticate(username="admin", password="admin123")
    if user:
        print("  Password 'admin123' is CORRECT")
    else:
        print("  Password 'admin123' is INCORRECT")
else:
    print("No admin account found")

# Check admin character
admin_char = ObjectDB.objects.filter(db_key__iexact="admin", db_typeclass_path__contains="Character").first()
if admin_char:
    print(f"\nAdmin character found: {admin_char}")
    print(f"  DB ID: {admin_char.id}")
    print(f"  Typeclass: {admin_char.db_typeclass_path}")
else:
    print("\nNo admin character found")