#!/usr/bin/env python3
"""
Test script to connect to Evennia WebSocket and test commands.
"""
import asyncio
import websockets
import json
import sys

WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app"
USERNAME = "admin"
PASSWORD = "admin123"

class EvenniaTestClient:
    def __init__(self, url):
        self.url = url
        self.websocket = None
        self.logged_in = False
        self.messages = []
        self.csessid = None

    async def connect(self):
        print(f"Connecting to {self.url}...")
        try:
            self.websocket = await websockets.connect(
                self.url,
                ping_interval=20,
                ping_timeout=10
            )
            print("Connected!")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def receive_message(self, timeout=5):
        """Wait for a message with timeout."""
        try:
            msg = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )
            data = json.loads(msg)
            self.messages.append(data)
            return data
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            print(f"Error receiving: {e}")
            return None

    async def send_command(self, cmd):
        """Send a command to the server."""
        msg = json.dumps([
            "text",
            cmd,
            {}
        ])
        print(f">>> Sending: {cmd}")
        await self.websocket.send(msg)

    async def login(self, username, password):
        """Login to the game."""
        # Wait for initial connection message
        print("Waiting for connection confirmation...")
        for _ in range(10):
            msg = await self.receive_message()
            if msg:
                print(f"<<< Received: {msg}")
                if msg[0] == "csessid":
                    self.csessid = msg[1]
                    print(f"Got csessid: {self.csessid}")
                    break
                elif msg[0] == "text":
                    if "connect" in str(msg).lower() or "login" in str(msg).lower():
                        break
            await asyncio.sleep(0.5)

        # Send login command
        login_cmd = f"connect {username} {password}"
        await self.send_command(login_cmd)

        # Wait for login response
        print("Waiting for login response...")
        for _ in range(20):
            msg = await self.receive_message(timeout=10)
            if msg:
                print(f"<<< Received: {json.dumps(msg, ensure_ascii=False)[:500]}")
                if msg[0] == "text":
                    text = msg[1]
                    if "Welcome" in text or "connected" in text.lower():
                        self.logged_in = True
                        print("Login successful!")
                        return True
                    elif "incorrect" in text.lower() or "invalid" in text.lower():
                        print("Login failed - incorrect credentials")
                        return False
                    elif "already exists" in text.lower():
                        # Character already logged in
                        self.logged_in = True
                        print("Already logged in")
                        return True
            await asyncio.sleep(0.5)

        print("Login timeout - no response")
        return False

    async def test_command(self, cmd, expect_error=False):
        """Test a command and check for errors."""
        print(f"\n--- Testing command: {cmd} ---")
        await self.send_command(cmd)

        errors_found = []
        responses = []

        for _ in range(10):
            msg = await self.receive_message(timeout=5)
            if msg:
                responses.append(msg)
                if msg[0] == "text":
                    text = msg[1]
                    print(f"<<< {text[:200]}")
                    if "is not available" in text.lower():
                        errors_found.append(f"Command not available: {text}")
                    elif "error" in text.lower() or "not found" in text.lower():
                        if not expect_error:
                            errors_found.append(f"Error: {text}")
                    if len(text) > 10:  # Got a meaningful response
                        break
            await asyncio.sleep(0.3)

        return errors_found, responses

    async def close(self):
        if self.websocket:
            await self.websocket.close()


async def main():
    client = EvenniaTestClient(WEBSOCKET_URL)

    if not await client.connect():
        print("FAILED: Could not connect to WebSocket")
        return False

    try:
        # Test login
        if not await client.login(USERNAME, PASSWORD):
            print("FAILED: Could not login")
            return False

        # Wait a bit after login
        await asyncio.sleep(2)

        # Test @bbsub command - this should NOT error
        errors1, _ = await client.test_command("@bbsub")
        if errors1:
            print(f"\nFAILED: @bbsub command errors: {errors1}")
            return False

        await asyncio.sleep(1)

        # Test help command
        errors2, _ = await client.test_command("help")
        if errors2:
            print(f"\nFAILED: help command errors: {errors2}")
            return False

        await asyncio.sleep(1)

        # Test that the specific @bbsub/quiet story updates command works
        errors3, _ = await client.test_command("@bbsub/quiet story updates")
        if errors3:
            print(f"\nFAILED: @bbsub/quiet command errors: {errors3}")
            return False

        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)
        return True

    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)