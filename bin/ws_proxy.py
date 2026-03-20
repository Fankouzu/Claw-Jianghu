#!/usr/bin/env python3
"""
Simple WebSocket proxy for Evennia - simplified version.
"""
import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LISTEN_PORT = int(os.environ.get("PORT", 8080))
EVENNIA_HOST = "127.0.0.1"
EVENNIA_PORT = 4002


async def handle_client(reader, writer):
    """Handle incoming connection."""
    addr = writer.get_extra_info('peername')
    logger.info(f"Connection from {addr}")

    try:
        # Read initial request
        data = await asyncio.wait_for(reader.read(8192), timeout=10)
        if not data:
            logger.warning("No data received")
            writer.close()
            await writer.wait_closed()
            return

        request = data.decode('utf-8', errors='ignore')
        first_line = request.split('\r\n')[0] if '\r\n' in request else request
        logger.info(f"Request: {first_line}")

        # Handle HTTP health check
        if first_line.startswith('GET /health'):
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 2\r\n\r\nOK"
            writer.write(response.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            logger.info("Health check responded")
            return

        # For WebSocket upgrade, connect to Evennia
        logger.info(f"Connecting to Evennia at {EVENNIA_HOST}:{EVENNIA_PORT}")
        try:
            evennia_reader, evennia_writer = await asyncio.wait_for(
                asyncio.open_connection(EVENNIA_HOST, EVENNIA_PORT),
                timeout=10
            )
            logger.info("Connected to Evennia")
        except Exception as e:
            logger.error(f"Failed to connect to Evennia: {e}")
            response = "HTTP/1.1 502 Bad Gateway\r\nContent-Length: 21\r\n\r\nEvennia not available"
            writer.write(response.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # Forward initial request to Evennia
        evennia_writer.write(data)
        await evennia_writer.drain()
        logger.info("Forwarded initial request to Evennia")

        # Read response from Evennia
        response = await asyncio.wait_for(evennia_reader.read(8192), timeout=10)
        logger.info(f"Received response from Evennia: {len(response)} bytes")

        # Forward response to client
        writer.write(response)
        await writer.drain()
        logger.info("Forwarded response to client")

        # Set up bidirectional proxy
        async def forward(src, dst, direction):
            try:
                while True:
                    data = await src.read(8192)
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
            except Exception as e:
                logger.debug(f"Forward {direction} ended: {e}")

        # Run both directions
        await asyncio.gather(
            forward(reader, evennia_writer, "client->evennia"),
            forward(evennia_reader, writer, "evennia->client")
        )

    except asyncio.TimeoutError:
        logger.warning("Connection timeout")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass
        logger.info("Connection closed")


async def main():
    logger.info(f"Starting WebSocket proxy on 0.0.0.0:{LISTEN_PORT}")
    logger.info(f"Forwarding to Evennia at {EVENNIA_HOST}:{EVENNIA_PORT}")

    server = await asyncio.start_server(handle_client, '0.0.0.0', LISTEN_PORT)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())