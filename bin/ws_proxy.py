#!/usr/bin/env python3
"""
Simple WebSocket proxy for Evennia.
Receives WSS connections and forwards to Evennia's WebSocket server.
"""
import asyncio
import os
import websockets
import ssl
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EVENNIA_WS_HOST = "127.0.0.1"
EVENNIA_WS_PORT = 4002
LISTEN_PORT = int(os.environ.get("PORT", 8080))


async def proxy_handler(client_ws, path):
    """Handle WebSocket proxying between client and Evennia."""
    logger.info(f"New connection from {client_ws.remote_address}")

    try:
        # Connect to Evennia's WebSocket server
        async with websockets.connect(
            f"ws://{EVENNIA_WS_HOST}:{EVENNIA_WS_PORT}",
            ping_interval=20,
            ping_timeout=10
        ) as evennia_ws:
            logger.info("Connected to Evennia WebSocket server")

            async def forward_to_evennia():
                """Forward messages from client to Evennia."""
                try:
                    async for message in client_ws:
                        logger.debug(f"Client -> Evennia: {message[:100]}")
                        await evennia_ws.send(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding to Evennia: {e}")

            async def forward_to_client():
                """Forward messages from Evennia to client."""
                try:
                    async for message in evennia_ws:
                        logger.debug(f"Evennia -> Client: {message[:100]}")
                        await client_ws.send(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding to client: {e}")

            # Run both directions concurrently
            await asyncio.gather(
                forward_to_evennia(),
                forward_to_client()
            )

    except Exception as e:
        logger.error(f"Proxy error: {e}")
    finally:
        logger.info("Connection closed")


async def main():
    logger.info(f"Starting WebSocket proxy on port {LISTEN_PORT}")
    logger.info(f"Forwarding to Evennia at {EVENNIA_WS_HOST}:{EVENNIA_WS_PORT}")

    async with websockets.serve(
        proxy_handler,
        "0.0.0.0",
        LISTEN_PORT,
        ping_interval=20,
        ping_timeout=20
    ):
        logger.info("WebSocket proxy started")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())