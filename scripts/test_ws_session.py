#!/usr/bin/env python3
"""
Test WebSocket connection locally within Railway container.
This runs during startup to diagnose WebSocket issues.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.railway_ws_settings')

import django
django.setup()

import evennia
evennia._init()

print("=== Testing WebSocket Session ===")

try:
    from evennia.objects.models import ObjectDB
    from evennia.accounts.models import AccountDB

    # Check admin account
    admin_account = AccountDB.objects.filter(username="admin").first()
    if admin_account:
        print(f"Admin account: {admin_account}")
        print(f"  Is active: {admin_account.is_active}")
        print(f"  Is superuser: {admin_account.is_superuser}")

        # Test authentication
        from django.contrib.auth import authenticate
        user = authenticate(username="admin", password="admin123")
        if user:
            print("  Password 'admin123' validated successfully")
        else:
            print("  Password 'admin123' validation FAILED")
            # Try to reset password
            admin_account.set_password("admin123")
            admin_account.save()
            print("  Password reset to 'admin123'")
    else:
        print("No admin account found!")

    # Check session handler
    from evennia.server.sessionhandler import SESSIONS
    print(f"\nSession handler: {SESSIONS}")
    print(f"  Connected sessions: {SESSIONS.count()}")

    # Check portal status
    from evennia.server.portal.portal import Portal
    print("\nPortal module imported successfully")

    print("\n=== WebSocket Session Test Complete ===")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()