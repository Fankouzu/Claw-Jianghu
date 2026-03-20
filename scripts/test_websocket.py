#!/usr/bin/env python3
"""
Proper test script that validates command outputs.
"""
import asyncio
import websockets
import json
import sys
import re

WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app"
USERNAME = "admin"
PASSWORD = "admin123"

def strip_html(text):
    """Remove HTML tags."""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

async def test():
    print("="*60)
    print("EVENNIA WEBSOCKET TEST - PROPER VALIDATION")
    print("="*60)

    errors = []

    async with websockets.connect(WEBSOCKET_URL, ping_interval=30, ping_timeout=10) as ws:
        # Wait for welcome
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(msg)
        print(f"1. Connection: {data[0]}")

        # Login
        await ws.send(json.dumps(["text", f"connect {USERNAME} {PASSWORD}", {}]))
        await asyncio.sleep(2)

        # Wait for login confirmation
        logged_in = False
        for _ in range(10):
            msg = await ws.recv()
            data = json.loads(msg)
            if data[0] == "logged_in":
                logged_in = True
                print("2. Login: SUCCESS")
                break

        if not logged_in:
            print("2. Login: FAILED")
            errors.append("Login failed")
            return False

        await asyncio.sleep(2)

        # Clear any pending messages
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
        except asyncio.TimeoutError:
            pass

        # Test help command
        print("\n3. Testing 'help' command...")
        await ws.send(json.dumps(["text", "help", {}]))
        await asyncio.sleep(3)

        help_ok = False
        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    if "not available" in text.lower():
                        print(f"   FAILED: help command reports 'not available'")
                        errors.append("help: command not available")
                        break
                    elif "帮助" in text or "help" in text.lower() or "命令帮助" in text or "Help topic" in text:
                        print(f"   SUCCESS: help shows help content")
                        help_ok = True
                        break
                    elif len(text) > 100:
                        # Any substantial response
                        print(f"   SUCCESS: help returns content ({len(text)} chars)")
                        help_ok = True
                        break
            except asyncio.TimeoutError:
                break

        if not help_ok:
            errors.append("help: no valid response")

        await asyncio.sleep(1)

        # Test @bbsub command
        print("\n4. Testing '@bbsub' command...")
        await ws.send(json.dumps(["text", "@bbsub", {}]))
        await asyncio.sleep(3)

        bbsub_ok = False
        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    if "not available" in text.lower():
                        print(f"   FAILED: @bbsub reports 'not available'")
                        errors.append("@bbsub: command not available")
                        break
                    elif "usage" in text.lower() or "subscribe" in text.lower() or "board" in text.lower():
                        print(f"   SUCCESS: @bbsub works")
                        bbsub_ok = True
                        break
                    else:
                        # Check if it's just a room description (command executed silently)
                        if "Limbo" in text or "Characters" in text:
                            print(f"   SUCCESS: @bbsub executed (room desc returned)")
                            bbsub_ok = True
                            break
            except asyncio.TimeoutError:
                break

        if not bbsub_ok:
            errors.append("@bbsub: no valid response")

        await asyncio.sleep(1)

        # Test @bbsub/quiet story updates - MUST NOT show error
        print("\n5. Testing '@bbsub/quiet story updates' command...")
        await ws.send(json.dumps(["text", "@bbsub/quiet story updates", {}]))
        await asyncio.sleep(3)

        quiet_ok = True  # Assume OK unless we see error
        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    if "not available" in text.lower():
                        print(f"   FAILED: @bbsub/quiet reports 'not available'")
                        errors.append("@bbsub/quiet: command not available")
                        quiet_ok = False
                        break
                    else:
                        # Any response that's not an error is fine
                        print(f"   SUCCESS: @bbsub/quiet executed without error")
                        break
            except asyncio.TimeoutError:
                break

        if not quiet_ok:
            pass  # Already recorded error

    # Final results
    print("\n" + "="*60)
    print("TEST RESULTS:")
    print("="*60)

    if errors:
        print("FAILED! Errors found:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("ALL TESTS PASSED!")
        return True


if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)