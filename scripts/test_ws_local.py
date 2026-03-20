#!/usr/bin/env python3
"""
Test WebSocket login directly on Railway server.
This runs inside the Railway container to diagnose WebSocket issues.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.railway_ws_settings')

import django
django.setup()

import evennia
evennia._init()

print("=== Testing WebSocket Login ===")

try:
    from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol
    from twisted.internet import reactor, defer
    from twisted.internet.protocol import ReconnectingClientFactory

    class TestProtocol(WebSocketClientProtocol):
        def onOpen(self):
            print("WebSocket connected!")
            # Send login command
            import json
            msg = json.dumps(["text", ["connect admin admin123"]])
            print(f"Sending: {msg}")
            self.sendMessage(msg.encode('utf-8'))

        def onMessage(self, payload, isBinary):
            print(f"Received: {payload[:200]}...")

        def onClose(self, wasClean, code, reason):
            print(f"Closed: wasClean={wasClean}, code={code}, reason={reason}")
            reactor.stop()

    class TestFactory(WebSocketClientFactory, ReconnectingClientFactory):
        protocol = TestProtocol

        def clientConnectionFailed(self, connector, reason):
            print(f"Connection failed: {reason}")
            reactor.stop()

        def clientConnectionLost(self, connector, reason):
            print(f"Connection lost: {reason}")
            reactor.stop()

    factory = TestFactory("ws://127.0.0.1:8001")
    reactor.connectTCP("127.0.0.1", 8001, factory)

    # Set timeout
    reactor.callLater(10, reactor.stop)

    print("Starting reactor...")
    reactor.run()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()