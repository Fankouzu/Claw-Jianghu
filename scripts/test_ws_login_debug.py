#!/usr/bin/env python3
"""
Test WebSocket login with detailed debugging.
This script runs on Railway to diagnose WebSocket login issues.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.railway_ws_settings')

import django
django.setup()

import evennia
evennia._init()

print("=== Testing WebSocket Login Flow ===")

try:
    # Test 1: Check UnloggedinCmdSet
    print("\n1. Testing UnloggedinCmdSet...")
    from commands.default_cmdsets import UnloggedinCmdSet
    from evennia.commands.default import unloggedin

    cmdset = UnloggedinCmdSet()
    cmdset.at_cmdset_creation()

    cmds = list(cmdset.commands)
    print(f"   Commands found: {len(cmds)}")
    cmd_keys = [cmd.key for cmd in cmds]
    print(f"   Command keys: {cmd_keys[:20]}...")

    # Check for connect command
    connect_cmd = None
    for cmd in cmds:
        if cmd.key == "connect":
            connect_cmd = cmd
            break

    if connect_cmd:
        print(f"   Connect command found: {type(connect_cmd)}")
    else:
        print("   ERROR: No connect command found!")
        # Try to find any command with 'connect' in the name
        for cmd in cmds:
            if 'connect' in str(cmd.key).lower():
                print(f"   Found similar command: {cmd.key}")

    # Test 2: Test account authentication
    print("\n2. Testing account authentication...")
    from evennia.accounts.models import AccountDB
    from django.contrib.auth import authenticate

    admin = AccountDB.objects.filter(username="admin").first()
    if admin:
        print(f"   Admin account found: {admin.username}")
        print(f"   Is active: {admin.is_active}")

        user = authenticate(username="admin", password="admin123")
        if user:
            print("   Password 'admin123' verified: CORRECT")
        else:
            print("   Password 'admin123' verified: INCORRECT")
    else:
        print("   ERROR: No admin account found!")

    # Test 3: Test login command execution
    print("\n3. Testing login command execution...")
    from evennia.commands.cmdhandler import cmdhandler
    from evennia.server.serversession import ServerSession

    # Create a mock session
    class MockSession:
        def __init__(self):
            self.sessid = 999999
            self.logged_in = False
            self.account = None
            self.uid = None
            self.uname = ""
            self.puppet = None
            self.cmdset_storage = "commands.default_cmdsets.UnloggedinCmdSet"
            self.protocol_flags = {"UTF-8": True}
            self.sessionhandler = evennia.SERVER_SESSION_HANDLER
            self.messages = []

            # Set up cmdset handler
            from evennia.commands.cmdsethandler import CmdSetHandler
            self.cmdset = CmdSetHandler(self, True)
            self.cmdset.update(init_mode=True)

        def msg(self, text=None, **kwargs):
            if text:
                self.messages.append(str(text))
            print(f"   [MSG] {text}")

        def data_out(self, **kwargs):
            if 'text' in kwargs:
                text = kwargs['text']
                if isinstance(text, tuple) and len(text) > 0:
                    text = text[0]
                self.messages.append(str(text))
            print(f"   [DATA_OUT] {kwargs}")

        def update_session_counters(self, idle=False):
            pass

        def get_cmdset_providers(self):
            return {"session": self}

    mock_session = MockSession()

    # Execute connect command
    print("   Executing 'connect admin admin123'...")
    try:
        # Use cmdhandler directly
        result = cmdhandler(mock_session, "connect admin admin123", callertype="session", session=mock_session)
        print(f"   Command executed, result type: {type(result)}")

        # Wait a bit for async processing
        import time
        time.sleep(1)

        print(f"   Messages received: {len(mock_session.messages)}")
        for msg in mock_session.messages[:5]:
            print(f"   - {msg[:100] if len(msg) > 100 else msg}")

        # Check if login succeeded
        if mock_session.logged_in:
            print("   SUCCESS: Mock session is now logged in!")
        else:
            print("   Session not logged in after command")

    except Exception as e:
        print(f"   ERROR executing command: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Test the actual UnloggedinConnect command
    print("\n4. Testing CmdUnconnectedConnect directly...")
    try:
        from evennia.commands.default.unloggedin import CmdUnconnectedConnect

        cmd = CmdUnconnectedConnect()
        cmd.caller = mock_session
        cmd.session = mock_session
        cmd.raw_string = "connect admin admin123"
        cmd.args = "admin admin123"

        # Parse the args
        print(f"   Parsed args: '{cmd.args}'")

        # Try to parse using the command's parse method
        cmd.parse()

        # Try to execute
        print("   Calling cmd.func()...")
        cmd.func()

        print(f"   Messages after func: {mock_session.messages[-3:] if mock_session.messages else 'none'}")

    except Exception as e:
        print(f"   ERROR in direct command execution: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Complete ===")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()