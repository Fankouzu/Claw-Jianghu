#!/usr/bin/env python3
"""
WebSocket client test using correct Evennia protocol.
"""
import asyncio
import websockets
import json
import sys

WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app"

async def test():
    """Test WebSocket connection and login."""
    print(f"Connecting to {WEBSOCKET_URL}...")

    try:
        async with websockets.connect(
            WEBSOCKET_URL,
            ping_interval=30,
            ping_timeout=60,
            compression=None  # Disable compression to avoid extension issues
        ) as ws:
            print("Connected!")

            # Receive welcome message
            msg = await ws.recv()
            print(f"Welcome: {msg[:100]}...")

            # Send login command - Evennia expects [inputfunc_name, [args], {kwargs}]
            login_msg = json.dumps(["text", ["connect admin admin123"], {}])
            print(f"Sending login: {login_msg}")
            await ws.send(login_msg)

            # Collect responses
            responses = []
            try:
                for _ in range(10):
                    msg = await asyncio.wait_for(ws.recv(), timeout=2)
                    responses.append(msg)
                    print(f"Received: {msg[:100]}...")
            except asyncio.TimeoutError:
                pass

            # Check for logged_in
            for r in responses:
                try:
                    data = json.loads(r)
                    if "logged_in" in str(data):
                        print("Login successful!")

                        # Send help command - Evennia expects [inputfunc_name, [args], {kwargs}]
                        help_msg = json.dumps(["text", ["help"], {}])
                        await ws.send(help_msg)
                        print("Sent help command...")

                        # Collect help responses
                        help_responses = []
                        try:
                            for _ in range(15):
                                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                                help_responses.append(msg)
                        except asyncio.TimeoutError:
                            pass

                        # Parse help text
                        help_text = ""
                        for hr in help_responses:
                            try:
                                data = json.loads(hr)
                                if data[0] == "text":
                                    help_text += str(data[1])
                            except:
                                pass

                        print(f"\nHelp text ({len(help_text)} chars):")
                        print(help_text[:1500])

                        # Check for errors
                        if "AttributeError" in help_text or "TypeError" in help_text:
                            print("\nERROR: Error found in help!")
                            return False

                        if "not available" in help_text.lower():
                            print("\nERROR: 'not available' found!")
                            return False

                        # Check for commands
                        commands = ['look', 'inventory', 'help', 'say']
                        found = [c for c in commands if c in help_text.lower()]
                        if len(found) >= 2:
                            print(f"\nSUCCESS! Commands found: {found}")
                            return True

                        return False
                except:
                    pass

            print("Did not receive logged_in message")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    print(f"\nResult: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)