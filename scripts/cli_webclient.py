#!/usr/bin/env python3
"""
Command-line WebSocket client for Evennia.
Simulates the webclient behavior for testing.
Usage: python scripts/cli_webclient.py
"""
import asyncio
import websockets
import json
import sys
import readline  # For input history

WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app"

class EvenniaClient:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.logged_in = False
        self.running = True

    def strip_html(self, text):
        """Remove HTML tags from text for cleaner display."""
        import re
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<span[^>]*>', '', text)
        text = re.sub(r'</span>', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&amp;', '&', text)
        return text

    async def receive_messages(self):
        """Background task to receive and display messages."""
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                data = json.loads(msg)
                self.handle_message(data)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("\n[Connection closed]")
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"\n[Error receiving: {e}]")

    def handle_message(self, data):
        """Handle incoming message from server."""
        msg_type = data[0] if data else "unknown"

        if msg_type == "text":
            text = data[1]
            if isinstance(text, list):
                text = '\n'.join(self.strip_html(str(t)) for t in text)
            else:
                text = self.strip_html(str(text))
            print(f"\n{text}\n> ", end='', flush=True)

        elif msg_type == "logged_in":
            self.logged_in = True
            print("\n[Logged in successfully]\n> ", end='', flush=True)

        elif msg_type == "csessid":
            print(f"\n[Session ID: {data[1]}]\n> ", end='', flush=True)

        elif msg_type == "prompt":
            # Prompt message, usually not displayed
            pass

        else:
            print(f"\n[{msg_type}: {data}]\n> ", end='', flush=True)

    async def send_command(self, cmd):
        """Send a command to the server."""
        msg = json.dumps(["text", cmd, {}])
        await self.ws.send(msg)

    async def run(self):
        """Main client loop."""
        print(f"Connecting to {self.url}...")
        try:
            async with websockets.connect(self.url, ping_interval=30, ping_timeout=10) as ws:
                self.ws = ws
                print("Connected! Type 'quit' to exit.\n")

                # Start receive task
                receive_task = asyncio.create_task(self.receive_messages())

                # Wait a moment for initial messages
                await asyncio.sleep(1)

                # Input loop
                while self.running:
                    try:
                        cmd = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
                        cmd = cmd.strip()

                        if cmd.lower() == 'quit':
                            self.running = False
                            break

                        if cmd:
                            await self.send_command(cmd)

                    except EOFError:
                        self.running = False
                        break
                    except Exception as e:
                        print(f"Error: {e}")

                receive_task.cancel()

        except Exception as e:
            print(f"Connection error: {e}")
            return False

        return True


async def automated_test():
    """Run automated tests to verify WebSocket functionality."""
    print("="*60)
    print("AUTOMATED WEBSOCKET TEST")
    print("="*60)

    results = []

    async with websockets.connect(WEBSOCKET_URL, ping_interval=30, ping_timeout=10) as ws:
        # Wait for welcome
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(msg)
        print(f"1. Connection: {data[0]}")
        results.append(("Connection", data[0] == "text"))

        # Login
        await ws.send(json.dumps(["text", "connect admin admin123", {}]))
        await asyncio.sleep(2)

        # Read messages until logged_in
        for _ in range(5):
            msg = await ws.recv()
            data = json.loads(msg)
            if data[0] == "logged_in":
                print(f"2. Login: Success")
                results.append(("Login", True))
                break

        await asyncio.sleep(1)

        # Test help
        print("\n3. Testing 'help' command...")
        await ws.send(json.dumps(["text", "help", {}]))
        await asyncio.sleep(2)

        for _ in range(3):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    if "not available" in text.lower():
                        print(f"   FAILED: help command not available")
                        results.append(("help", False))
                    else:
                        print(f"   SUCCESS: help works")
                        results.append(("help", True))
                    break
            except asyncio.TimeoutError:
                results.append(("help", False))

        await asyncio.sleep(1)

        # Test @bbsub
        print("\n4. Testing '@bbsub' command...")
        await ws.send(json.dumps(["text", "@bbsub", {}]))
        await asyncio.sleep(2)

        for _ in range(3):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    if "not available" in text.lower():
                        print(f"   FAILED: @bbsub command not available")
                        results.append(("@bbsub", False))
                    else:
                        print(f"   SUCCESS: @bbsub works")
                        results.append(("@bbsub", True))
                    break
            except asyncio.TimeoutError:
                results.append(("@bbsub", False))

        await asyncio.sleep(1)

        # Test @bbsub/quiet story updates
        print("\n5. Testing '@bbsub/quiet story updates' command...")
        await ws.send(json.dumps(["text", "@bbsub/quiet story updates", {}]))
        await asyncio.sleep(2)

        for _ in range(3):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    text = str(data[1])
                    if "not available" in text.lower():
                        print(f"   FAILED: @bbsub/quiet not available")
                        results.append(("@bbsub/quiet", False))
                    else:
                        print(f"   SUCCESS: @bbsub/quiet works")
                        results.append(("@bbsub/quiet", True))
                    break
            except asyncio.TimeoutError:
                results.append(("@bbsub/quiet", False))

        await asyncio.sleep(1)

        # Test look
        print("\n6. Testing 'look' command...")
        await ws.send(json.dumps(["text", "look", {}]))
        await asyncio.sleep(2)

        for _ in range(3):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                if data[0] == "text":
                    print(f"   SUCCESS: look works")
                    results.append(("look", True))
                    break
            except asyncio.TimeoutError:
                results.append(("look", False))

    print("\n" + "="*60)
    print("TEST RESULTS:")
    print("="*60)
    all_passed = True
    for test, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")
        if not passed:
            all_passed = False

    print("="*60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("="*60)

    return all_passed


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(automated_test())
    else:
        print("Evennia WebSocket Client")
        print("Usage:")
        print("  python scripts/cli_webclient.py         # Interactive mode")
        print("  python scripts/cli_webclient.py --test  # Automated test")
        print()
        client = EvenniaClient(WEBSOCKET_URL)
        asyncio.run(client.run())


if __name__ == "__main__":
    main()