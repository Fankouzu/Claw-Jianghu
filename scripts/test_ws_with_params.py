#!/usr/bin/env python3
"""
Test WebSocket with the same URL format as webclient.
"""
import asyncio
import websockets
import json

# This is the actual URL format used by webclient
WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app?test_csessid&test_cuid&test_browser"

async def test():
    print(f"Testing URL: {WEBSOCKET_URL}")
    try:
        async with websockets.connect(WEBSOCKET_URL, ping_interval=30, ping_timeout=10) as ws:
            print("Connected!")
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(msg)
            print(f"Received: {data[0]}")

            # Login
            await ws.send(json.dumps(["text", "connect admin admin123", {}]))
            await asyncio.sleep(2)

            for _ in range(5):
                msg = await ws.recv()
                data = json.loads(msg)
                print(f"Received: {data[0]}")
                if data[0] == "logged_in":
                    print("Login successful!")
                    break

            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test())