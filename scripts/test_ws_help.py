#!/usr/bin/env python3
"""
WebSocket client test for Railway deployment.
Tests that the help command works correctly after login.
"""
import asyncio
import websockets
import json
import sys
import time

WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app"

async def test_help_command():
    """Test help command after login."""
    print(f"Connecting to {WEBSOCKET_URL}...")

    try:
        # Connect to WebSocket
        ws = await websockets.connect(
            WEBSOCKET_URL,
            ping_interval=30,
            ping_timeout=60
        )
        print("Connected!")

        try:
            # Wait for initial welcome message
            print("Waiting for welcome message...")
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            print(f"Welcome message received ({len(response)} chars)")

            # Send connect command using Evennia's JSON format
            # Format: ["text", ["connect username password"]]
            print("\nSending connect command...")
            msg = json.dumps(["text", ["connect admin admin123"]])
            await ws.send(msg)

            # Wait for login response
            print("Waiting for login response...")
            await asyncio.sleep(2)

            responses = []
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=3)
                    responses.append(response)
                except asyncio.TimeoutError:
                    break

            print(f"Received {len(responses)} responses after login")

            # Check for logged_in message
            logged_in = False
            for r in responses:
                try:
                    data = json.loads(r)
                    if data[0] == "logged_in":
                        logged_in = True
                        print("Login successful!")
                        break
                except:
                    pass

            if not logged_in:
                print("WARNING: Did not receive logged_in message")
                for r in responses[:3]:
                    print(f"  {r[:200]}")

            # Now test help command
            print("\nSending help command...")
            msg = json.dumps(["text", ["help"]])
            await ws.send(msg)

            # Collect help responses
            await asyncio.sleep(3)
            help_responses = []
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=3)
                    help_responses.append(response)
                except asyncio.TimeoutError:
                    break

            print(f"\nReceived {len(help_responses)} help responses")

            # Parse and check help output
            help_text = ""
            for r in help_responses:
                try:
                    data = json.loads(r)
                    if data[0] == "text":
                        help_text += str(data[1])
                except:
                    pass

            print(f"\nHelp text length: {len(help_text)} chars")
            print("=" * 50)
            # Print first 2000 chars
            print(help_text[:2000])
            print("=" * 50)

            # Check for errors
            if "AttributeError" in help_text:
                print("\nERROR: AttributeError found in help output!")
                return False

            if "TypeError" in help_text:
                print("\nERROR: TypeError found in help output!")
                return False

            if "not available" in help_text.lower():
                print("\nERROR: 'not available' found in help output!")
                return False

            # Check for expected commands
            expected_commands = ['look', 'inventory', 'help', 'say', 'get', 'pose']
            found_commands = [cmd for cmd in expected_commands if cmd in help_text.lower()]

            if len(found_commands) >= 3:
                print(f"\nSUCCESS: Help contains expected commands: {found_commands}")
                return True
            else:
                print(f"\nWARNING: Help may not contain enough commands. Found: {found_commands}")
                return False

        finally:
            await ws.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_help_command())
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)