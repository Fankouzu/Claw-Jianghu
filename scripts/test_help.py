#!/usr/bin/env python3
"""
Test help command execution directly on Railway database.
This script is run during Railway startup to diagnose help issues.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.railway_ws_settings')

import django
django.setup()

print("=== Testing Help Command ===")

try:
    import evennia
    evennia._init()

    from evennia.objects.models import ObjectDB
    from evennia.accounts.models import AccountDB
    from commands.default_cmdsets import CharacterCmdSet

    # Find admin character
    admin_char = ObjectDB.objects.filter(db_key__iexact="admin", db_typeclass_path__contains="Character").first()
    if admin_char:
        print(f"Found admin character: {admin_char}")

        # Get the character's cmdset
        print("Checking character's command set...")
        admin_char.cmdset.update(init_mode=True)

        if admin_char.cmdset.current:
            cmds = list(admin_char.cmdset.current.commands)
            print(f"Commands in current cmdset: {len(cmds)}")

            # Test access on each command
            errors = []
            working = []
            for cmd in cmds[:20]:  # Test first 20 commands
                try:
                    result = cmd.access(admin_char)
                    working.append((cmd.key, result))
                except Exception as e:
                    errors.append((cmd.key, str(e)))

            print(f"\nWorking commands (first 20): {[k for k, v in working[:10]]}")
            if errors:
                print(f"\nCommands with access errors:")
                for key, err in errors:
                    print(f"  {key}: {err}")
        else:
            print("No current cmdset!")
    else:
        print("No admin character found")

    # Now test the help command directly
    print("\n=== Testing Help Command Directly ===")
    from commands.base_commands.help import CmdHelp
    help_cmd = CmdHelp()
    help_cmd.caller = admin_char
    help_cmd.args = ""
    help_cmd.cmdset = admin_char.cmdset.current

    print("Running help.parse()...")
    help_cmd.parse()

    print("Running help.func()...")
    try:
        help_cmd.func()
        print("Help command executed successfully!")
    except Exception as e:
        print(f"Error in help.func(): {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()