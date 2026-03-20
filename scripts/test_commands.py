#!/usr/bin/env python3
"""
Test to check what commands are available after login.
"""
import asyncio
import websockets
import json
import sys
import re

WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app"

def strip_html(text):
    """Remove HTML tags."""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

async def test():
    print("Connecting...")
    async with websockets.connect(WEBSOCKET_URL, ping_interval=30, ping_timeout=10) as ws:
        # Wait for welcome
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        print(f"Received welcome")

        # Login
        await ws.send(json.dumps(["text", "connect admin admin123", {}]))
        await asyncio.sleep(2)

        # Wait for login
        for _ in range(10):
            msg = await ws.recv()
            data = json.loads(msg)
            if data[0] == "logged_in":
                print("Logged in!")
                break

        await asyncio.sleep(2)

        # Test 1: Check if @bbsub command exists
        print("\n1. Testing '@bbsub' command...")
        await ws.send(json.dumps(["text", "@bbsub", {}]))
        await asyncio.sleep(2)

        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    if "not available" in text.lower():
                        print(f"   FAILED: @bbsub command reports 'not available'")
                    else:
                        print(f"   SUCCESS: @bbsub command responded")
                        print(f"   Response: {text[:200]}...")
                    break
            except asyncio.TimeoutError:
                break

        await asyncio.sleep(1)

        # Test 2: Check help command for bbsub
        print("\n2. Testing 'help @bbsub' command...")
        await ws.send(json.dumps(["text", "help @bbsub", {}]))
        await asyncio.sleep(2)

        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    print(f"   Help response: {text[:300]}...")
                    break
            except asyncio.TimeoutError:
                break

        await asyncio.sleep(1)

        # Test 3: List available commands starting with @bb
        print("\n3. Testing '@bb' to see available bboard commands...")
        await ws.send(json.dumps(["text", "@bb", {}]))
        await asyncio.sleep(2)

        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    print(f"   Response: {text[:400]}...")
                    break
            except asyncio.TimeoutError:
                break

        await asyncio.sleep(1)

        # Test 4: Check help for all commands
        print("\n4. Testing 'help' to list all commands...")
        await ws.send(json.dumps(["text", "help", {}]))
        await asyncio.sleep(3)

        all_help = []
        for _ in range(15):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    all_help.append(text)
            except asyncio.TimeoutError:
                break

        full_help = "\n".join(all_help)
        if "bbsub" in full_help.lower():
            print("   SUCCESS: bbsub found in help")
        else:
            print("   FAILED: bbsub NOT found in help")

        print(f"\n   Full help output (first 1000 chars):\n{full_help[:1000]}")


if __name__ == "__main__":
    asyncio.run(test())