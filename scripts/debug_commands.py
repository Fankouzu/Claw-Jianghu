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

        # Try to see what commands are available by examining suggestions
        print("\nTrying to get command list...")

        # First, try the 'examine' command to see what cmdset we have
        await ws.send(json.dumps(["text", "examine self", {}]))
        await asyncio.sleep(2)

        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    print(f"Examine response: {text[:300]}...")
                    break
            except asyncio.TimeoutError:
                break

        await asyncio.sleep(1)

        # Try a basic command like 'look'
        print("\nTesting 'look' command...")
        await ws.send(json.dumps(["text", "look", {}]))
        await asyncio.sleep(2)

        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    if "not available" in text.lower():
                        print("ERROR: 'look' command not available!")
                    else:
                        print("SUCCESS: 'look' command works")
                        print(f"Response: {text[:200]}...")
                    break
            except asyncio.TimeoutError:
                break

        await asyncio.sleep(1)

        # Try help command and see what it suggests
        print("\nTesting 'help' command...")
        await ws.send(json.dumps(["text", "help", {}]))
        await asyncio.sleep(2)

        for _ in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    print(f"Help response: {text[:500]}")
                    break
            except asyncio.TimeoutError:
                break

        await asyncio.sleep(1)

        # Try @py to inspect cmdset (if we have permission)
        print("\nTrying to inspect command set...")
        await ws.send(json.dumps(["text", "@py self.cmdset", {}]))
        await asyncio.sleep(3)

        for _ in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    print(f"Cmdset info: {text[:500]}")
                    break
            except asyncio.TimeoutError:
                break


if __name__ == "__main__":
    asyncio.run(test())