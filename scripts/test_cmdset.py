#!/usr/bin/env python3
"""
Test to inspect the command set after login.
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
        await asyncio.sleep(3)

        # Wait for login
        for _ in range(10):
            msg = await ws.recv()
            data = json.loads(msg)
            if data[0] == "logged_in":
                print("Logged in!")
                break

        await asyncio.sleep(2)

        # Use @py to inspect the command set
        print("\n1. Inspecting character's command set...")
        await ws.send(json.dumps(["text", "@py self.cmdset", {}]))
        await asyncio.sleep(3)

        all_responses = []
        for _ in range(15):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    all_responses.append(text)
            except asyncio.TimeoutError:
                break

        print(f"Response:\n{chr(10).join(all_responses)}")

        await asyncio.sleep(1)

        # List all commands in the merged command set
        print("\n2. Listing commands in the merged command set...")
        await ws.send(json.dumps(["text", "@py [cmd.key for cmd in self.cmdset]", {}]))
        await asyncio.sleep(3)

        all_responses = []
        for _ in range(15):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    all_responses.append(text)
            except asyncio.TimeoutError:
                break

        print(f"Response:\n{chr(10).join(all_responses)}")

        await asyncio.sleep(1)

        # Check if OOCCmdSet exists
        print("\n3. Checking OOCCmdSet...")
        await ws.send(json.dumps(["text", "@py from commands.cmdsets.standard import OOCCmdSet; print(OOCCmdSet)", {}]))
        await asyncio.sleep(3)

        all_responses = []
        for _ in range(15):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = strip_html(str(data[1]))
                    all_responses.append(text)
            except asyncio.TimeoutError:
                break

        print(f"Response:\n{chr(10).join(all_responses)}")


if __name__ == "__main__":
    asyncio.run(test())