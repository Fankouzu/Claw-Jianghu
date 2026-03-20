#!/usr/bin/env python3
"""
Reset command sets for admin character.
This script is run during Railway startup to fix command set issues.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.railway_ws_settings')

import django
django.setup()

import evennia
evennia._init()

from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB

print("=== Resetting Command Sets ===")

try:
    # Find admin account
    admin_account = AccountDB.objects.filter(username="admin").first()
    if admin_account:
        print(f"Found admin account: {admin_account}")
        # Reset account's command set storage
        admin_account.cmdset_storage = ["commands.default_cmdsets.AccountCmdSet"]
        admin_account.save()
        print("Reset admin account command set storage")

        # Reinitialize cmdset handler
        admin_account.cmdset.update(init_mode=True)
        print(f"Account commands available: {len(list(admin_account.cmdset.current.commands)) if admin_account.cmdset.current else 0}")
    else:
        print("No admin account found")

    # Find admin character
    admin_char = ObjectDB.objects.filter(db_key__iexact="admin", db_typeclass_path__contains="Character").first()
    if admin_char:
        print(f"Found admin character: {admin_char}")
        # Reset character's command set storage
        admin_char.cmdset_storage = ["commands.default_cmdsets.CharacterCmdSet"]
        admin_char.save()
        print("Reset admin character command set storage")

        # Reinitialize cmdset handler
        admin_char.cmdset.update(init_mode=True)
        print(f"Character commands available: {len(list(admin_char.cmdset.current.commands)) if admin_char.cmdset.current else 0}")
    else:
        print("No admin character found")

    print("=== Command Set Reset Complete ===")

except Exception as e:
    print(f"Error resetting command sets: {e}")
    import traceback
    traceback.print_exc()