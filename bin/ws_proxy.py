#!/usr/bin/env python3
"""
HTTP + WebSocket proxy for Evennia.
Handles both HTTP requests and WebSocket upgrades.
"""
import asyncio
import os
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LISTEN_PORT = int(os.environ.get("PORT", 4002))
EVENNIA_HTTP_HOST = "127.0.0.1"
EVENNIA_HTTP_PORT = 4001  # Evennia's internal HTTP port
EVENNIA_WS_HOST = "127.0.0.1"
EVENNIA_WS_PORT = 8001  # Evennia's WebSocket port (changed from 4002)


async def proxy_websocket(reader, writer):
    """Handle WebSocket connection by proxying to Evennia's WebSocket server."""
    logger.info("Setting up WebSocket proxy to Evennia")

    try:
        # Connect to Evennia's WebSocket server
        evennia_reader, evennia_writer = await asyncio.wait_for(
            asyncio.open_connection(EVENNIA_WS_HOST, EVENNIA_WS_PORT),
            timeout=10
        )
        logger.info("Connected to Evennia WebSocket")

        # Set up bidirectional proxy
        async def forward(src, dst, direction):
            try:
                while True:
                    data = await src.read(8192)
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
                    logger.debug(f"Forwarded {len(data)} bytes {direction}")
            except Exception as e:
                logger.debug(f"Forward {direction} ended: {e}")

        await asyncio.gather(
            forward(reader, evennia_writer, "client->evennia"),
            forward(evennia_reader, writer, "evennia->client")
        )

    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
    finally:
        logger.info("WebSocket proxy connection closed")


async def handle_http_request(reader, writer, request_data):
    """Handle regular HTTP request by proxying to Evennia's HTTP server."""
    try:
        # Connect to Evennia's HTTP server
        http_reader, http_writer = await asyncio.wait_for(
            asyncio.open_connection(EVENNIA_HTTP_HOST, EVENNIA_HTTP_PORT),
            timeout=10
        )

        # Forward the request
        http_writer.write(request_data)
        await http_writer.drain()

        # Read and forward response
        while True:
            data = await http_reader.read(8192)
            if not data:
                break
            writer.write(data)
            await writer.drain()

        http_writer.close()
        await http_writer.wait_closed()

    except Exception as e:
        logger.error(f"HTTP proxy error: {e}")
        writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        await writer.drain()

    writer.close()
    await writer.wait_closed()


async def handle_client(reader, writer):
    """Handle incoming client connection."""
    addr = writer.get_extra_info('peername')
    logger.info(f"New connection from {addr}")

    try:
        # Read the initial request
        data = await asyncio.wait_for(reader.read(8192), timeout=30)
        if not data:
            logger.warning("No data received")
            writer.close()
            await writer.wait_closed()
            return

        request_str = data.decode('utf-8', errors='ignore')
        first_line = request_str.split('\r\n')[0] if '\r\n' in request_str else request_str[:100]
        logger.info(f"Request: {first_line}")

        # Parse headers
        headers = {}
        lines = request_str.split('\r\n')
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        # Check if this is a WebSocket upgrade request
        is_websocket = (
            headers.get('upgrade', '').lower() == 'websocket' and
            headers.get('connection', '').lower() in ['upgrade', 'keep-alive, upgrade']
        )

        if is_websocket:
            logger.info("WebSocket upgrade detected")
            # For WebSocket, we need to handle the upgrade differently
            # Evennia's WebSocket server expects raw WebSocket frames, not HTTP upgrade

            # Send WebSocket accept response
            import hashlib
            import base64
            ws_key = headers.get('sec-websocket-key', '')
            magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept_key = base64.b64encode(
                hashlib.sha1((ws_key + magic).encode()).digest()
            ).decode()

            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n"
                "\r\n"
            )
            writer.write(response.encode())
            await writer.drain()
            logger.info("Sent WebSocket upgrade response")

            # Now proxy WebSocket frames
            await proxy_websocket(reader, writer)

        else:
            # Regular HTTP request
            await handle_http_request(reader, writer, data)

    except asyncio.TimeoutError:
        logger.warning("Connection timeout")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        logger.error(f"Error handling connection: {e}")
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass


async def main():
    logger.info(f"Starting HTTP+WebSocket proxy on 0.0.0.0:{LISTEN_PORT}")
    logger.info(f"HTTP proxy to {EVENNIA_HTTP_HOST}:{EVENNIA_HTTP_PORT}")
    logger.info(f"WebSocket proxy to {EVENNIA_WS_HOST}:{EVENNIA_WS_PORT}")

    server = await asyncio.start_server(handle_client, '0.0.0.0', LISTEN_PORT)
    addr = server.sockets[0].getsockname()
    logger.info(f"Proxy listening on {addr}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())