#!/usr/bin/env python3
"""
Test connect command directly on Railway.
This runs inside the Railway container to diagnose login issues.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.railway_ws_settings')

import django
django.setup()

import evennia
evennia._init()

print("=== Testing Connect Command ===")

try:
    # Import command sets
    from commands.default_cmdsets import UnloggedinCmdSet
    from evennia.commands.default.unloggedin import CmdUnconnectedConnect

    # Create command set
    print("Creating UnloggedinCmdSet...")
    cmdset = UnloggedinCmdSet()
    cmdset.at_cmdset_creation()

    # List commands
    cmds = list(cmdset.commands)
    print(f"Commands in UnloggedinCmdSet: {len(cmds)}")
    for cmd in cmds:
        print(f"  - {cmd.key}")

    # Check for connect command
    connect_cmd = None
    for cmd in cmds:
        if cmd.key == "connect":
            connect_cmd = cmd
            break

    if connect_cmd:
        print(f"\nConnect command found: {connect_cmd}")
        print(f"  Type: {type(connect_cmd)}")
    else:
        print("\nWARNING: No connect command found!")

    # Test account authentication
    from evennia.accounts.models import AccountDB
    from django.contrib.auth import authenticate

    admin = AccountDB.objects.filter(username="admin").first()
    if admin:
        print(f"\nAdmin account found: {admin}")
        print(f"  Is active: {admin.is_active}")
        print(f"  Is superuser: {admin.is_superuser}")

        # Test password
        user = authenticate(username="admin", password="admin123")
        if user:
            print("  Password 'admin123' is CORRECT")
        else:
            print("  Password 'admin123' is INCORRECT")
    else:
        print("\nNo admin account found!")

    print("\n=== Test Complete ===")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()