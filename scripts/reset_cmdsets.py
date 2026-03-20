#!/usr/bin/env python3
"""
Test to reset command sets.
"""
import asyncio
import websockets
import json
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
        await asyncio.sleep(3)

        # Wait for login
        for _ in range(10):
            msg = await ws.recv()
            data = json.loads(msg)
            if data[0] == "logged_in":
                print("Logged in!")
            elif data[0] == "text":
                text = strip_html(str(data[1]))
                if "become admin" in text or "Limbo" in text:
                    print(f"  {text[:100]}")

        await asyncio.sleep(2)

        # Drain any remaining messages
        for _ in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
            except asyncio.TimeoutError:
                break

        # Try @typeclass/force/reset to reset the character's command sets
        print("\n1. Testing '@typeclass/force/reset admin' command...")
        await ws.send(json.dumps(["text", "@typeclass/force/reset admin", {}]))
        await asyncio.sleep(5)

        all_responses = []
        for _ in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    all_responses.append(text)
            except asyncio.TimeoutError:
                break

        print(f"Response: {all_responses[:3]}")  # Only show first 3 to avoid spam

        await asyncio.sleep(2)

        # Try look command after reset
        print("\n2. Testing 'look' command after reset...")
        await ws.send(json.dumps(["text", "look", {}]))
        await asyncio.sleep(2)

        all_responses = []
        for _ in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    all_responses.append(text)
            except asyncio.TimeoutError:
                break

        print(f"Response: {all_responses}")


if __name__ == "__main__":
    asyncio.run(test())
