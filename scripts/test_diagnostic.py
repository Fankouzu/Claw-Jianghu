#!/usr/bin/env python3
"""
Diagnostic script to check command set state on the Railway server.
Tests what's happening with command sets at different levels.
"""
import asyncio
import websockets
import json
import re
import sys

WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app"

def strip_html(text):
    """Remove HTML tags."""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

async def test():
    print("=" * 60)
    print("COMMAND SET DIAGNOSTIC TEST")
    print("=" * 60)

    try:
        async with websockets.connect(WEBSOCKET_URL, ping_interval=30, ping_timeout=10, close_timeout=5) as ws:
            # Wait for welcome
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"Connected: {msg[:50]}...")

            # Login
            await ws.send(json.dumps(["text", "connect admin admin123", {}]))
            print("Sent login credentials...")

            # Collect all login messages
            logged_in = False
            for i in range(15):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    data = json.loads(msg)
                    if data[0] == "logged_in":
                        logged_in = True
                        print("\n✓ LOGGED IN SUCCESSFULLY")
                    elif data[0] == "text":
                        text = strip_html(str(data[1]))
                        # Check for important messages
                        if "become admin" in text.lower():
                            print(f"\n✓ CHARACTER PUPPETED: {text[:100]}")
                        elif "not available" in text.lower():
                            print(f"\n✗ COMMAND ERROR: {text[:100]}")
                except asyncio.TimeoutError:
                    break

            if not logged_in:
                print("\n✗ FAILED TO LOGIN")
                return

            await asyncio.sleep(2)

            # Drain remaining messages
            for i in range(5):
                try:
                    await asyncio.wait_for(ws.recv(), timeout=1)
                except asyncio.TimeoutError:
                    break

            # Test 1: Check account level commands
            print("\n" + "=" * 60)
            print("TEST 1: Account-level commands (should work before IC)")
            print("=" * 60)

            account_cmds = ["ooc", "who", "@password", "@option"]
            for cmd in account_cmds:
                await ws.send(json.dumps(["text", cmd, {}]))
                await asyncio.sleep(1)
                result = await get_response(ws)
                if "not available" in result.lower():
                    print(f"  ✗ '{cmd}' - NOT AVAILABLE")
                else:
                    print(f"  ✓ '{cmd}' - works")

            # Test 2: Try IC to puppet character
            print("\n" + "=" * 60)
            print("TEST 2: IC command to puppet character")
            print("=" * 60)

            await ws.send(json.dumps(["text", "ic admin", {}]))
            await asyncio.sleep(2)
            result = await get_response(ws)
            print(f"  IC result: {result[:150]}")

            # Test 3: Character-level commands
            print("\n" + "=" * 60)
            print("TEST 3: Character-level commands (should work after IC)")
            print("=" * 60)

            char_cmds = ["look", "inventory", "help", "say hello"]
            for cmd in char_cmds:
                await ws.send(json.dumps(["text", cmd, {}]))
                await asyncio.sleep(1)
                result = await get_response(ws)
                if "not available" in result.lower():
                    print(f"  ✗ '{cmd}' - NOT AVAILABLE")
                else:
                    print(f"  ✓ '{cmd}' - works")

            # Test 4: Staff commands
            print("\n" + "=" * 60)
            print("TEST 4: Staff commands")
            print("=" * 60)

            staff_cmds = ["@py 1+1", "@examine me", "@teleport"]
            for cmd in staff_cmds:
                await ws.send(json.dumps(["text", cmd, {}]))
                await asyncio.sleep(1)
                result = await get_response(ws)
                if "not available" in result.lower():
                    print(f"  ✗ '{cmd}' - NOT AVAILABLE")
                else:
                    print(f"  ✓ '{cmd}' - works (or partial)")

            # Test 5: Bulletin board commands
            print("\n" + "=" * 60)
            print("TEST 5: Bulletin board commands")
            print("=" * 60)

            bb_cmds = ["@bbsub", "@bbnew", "@bb"]
            for cmd in bb_cmds:
                await ws.send(json.dumps(["text", cmd, {}]))
                await asyncio.sleep(1)
                result = await get_response(ws)
                if "not available" in result.lower():
                    print(f"  ✗ '{cmd}' - NOT AVAILABLE")
                else:
                    print(f"  ✓ '{cmd}' - works")

            # Summary
            print("\n" + "=" * 60)
            print("DIAGNOSTIC COMPLETE")
            print("=" * 60)
            print("If most commands show 'NOT AVAILABLE', the command set")
            print("is not being properly attached to the character/account.")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

async def get_response(ws, timeout=3):
    """Get response from websocket."""
    responses = []
    for i in range(5):
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
            data = json.loads(msg)
            if data[0] == "text":
                responses.append(strip_html(str(data[1])))
        except asyncio.TimeoutError:
            break
    return " | ".join(responses)[:500]

if __name__ == "__main__":
    asyncio.run(test())