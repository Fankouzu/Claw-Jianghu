#!/usr/bin/env python3
"""
Test to reset command sets on the admin character.
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
                print(f"  Text: {text[:100]}")

        await asyncio.sleep(2)

        # Drain any remaining messages
        for _ in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
            except asyncio.TimeoutError:
                break

        # Try to reset command sets using @quell
        print("\n1. Testing '@quell' command...")
        await ws.send(json.dumps(["text", "@quell", {}]))
        await asyncio.sleep(3)

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

        await asyncio.sleep(1)

        # Try to examine the character
        print("\n2. Testing '@examine me' command...")
        await ws.send(json.dumps(["text", "@examine me", {}]))
        await asyncio.sleep(3)

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

        await asyncio.sleep(1)

        # Try look command
        print("\n3. Testing 'look' command...")
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