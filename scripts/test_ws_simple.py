#!/usr/bin/env python3
"""
Simple WebSocket test using websocket-client library.
"""
import websocket
import json
import time
import sys
import threading

WEBSOCKET_URL = "wss://claw-jianghu-ws.up.railway.app"
received_messages = []

def on_message(ws, message):
    print(f"Received: {message[:500]}...")
    received_messages.append(message)

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Connection closed: code={close_status_code}, msg={close_msg}")

def on_open(ws):
    print("Connection opened, waiting for welcome message...")
    # Wait for welcome message
    time.sleep(2)

    # Send connect command
    msg = json.dumps(["text", ["connect admin admin123"]])
    print(f"Sending: {msg}")
    ws.send(msg)

    # Wait for response
    time.sleep(3)
    print(f"Received {len(received_messages)} messages so far")

    if len(received_messages) == 0:
        print("No response received, connection might have been closed")
        return

    # Send help command
    msg = json.dumps(["text", ["help"]])
    print(f"Sending: {msg}")
    ws.send(msg)

    # Wait for response
    time.sleep(3)
    print(f"Total received: {len(received_messages)} messages")

    # Close after test
    ws.close()

if __name__ == "__main__":
    print(f"Connecting to {WEBSOCKET_URL}...")

    # Create WebSocket connection
    ws = websocket.WebSocketApp(
        WEBSOCKET_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    # Run the WebSocket with a timeout
    ws.run_forever(ping_interval=30)