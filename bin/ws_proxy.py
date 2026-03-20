#!/usr/bin/env python3
"""
HTTP + WebSocket proxy for Evennia.
Transparently forwards both HTTP and WebSocket connections.
"""
import asyncio
import os
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LISTEN_PORT = int(os.environ.get("PORT", 4002))
EVENNIA_WS_HOST = "127.0.0.1"
EVENNIA_WS_PORT = 8001  # Evennia's WebSocket port


async def handle_client(reader, writer):
    """Handle incoming client connection - transparently forward to Evennia WebSocket."""
    addr = writer.get_extra_info('peername')
    logger.info(f"New connection from {addr}")

    try:
        # Read initial request to check if it's HTTP or raw
        data = await asyncio.wait_for(reader.read(8192), timeout=30)
        if not data:
            logger.warning("No data received")
            writer.close()
            await writer.wait_closed()
            return

        request_str = data.decode('utf-8', errors='ignore')
        first_line = request_str.split('\r\n')[0] if '\r\n' in request_str else request_str[:100]
        logger.info(f"Request: {first_line}")

        # Parse headers to check for WebSocket upgrade
        headers = {}
        lines = request_str.split('\r\n')
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        # Log all headers for debugging
        logger.info(f"Headers: {headers}")

        is_websocket = headers.get('upgrade', '').lower() == 'websocket'
        logger.info(f"WebSocket upgrade: {is_websocket}")

        # Connect to Evennia's WebSocket server
        logger.info(f"Connecting to Evennia at {EVENNIA_WS_HOST}:{EVENNIA_WS_PORT}")
        try:
            evennia_reader, evennia_writer = await asyncio.wait_for(
                asyncio.open_connection(EVENNIA_WS_HOST, EVENNIA_WS_PORT),
                timeout=10
            )
            logger.info("Connected to Evennia WebSocket")
        except Exception as e:
            logger.error(f"Failed to connect to Evennia: {e}")
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\nEvennia not available")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # Forward the initial request to Evennia
        evennia_writer.write(data)
        await evennia_writer.drain()
        logger.info("Forwarded initial request to Evennia")

        # If WebSocket upgrade, we need to read Evennia's response first
        if is_websocket:
            # Read Evennia's HTTP 101 response
            response = await asyncio.wait_for(evennia_reader.read(8192), timeout=10)
            logger.info(f"Received response from Evennia: {len(response)} bytes")
            # Forward response to client
            writer.write(response)
            await writer.drain()
            logger.info("Forwarded WebSocket upgrade response to client")

        # Set up bidirectional proxy
        async def forward(src, dst, direction):
            try:
                while True:
                    data = await src.read(8192)
                    if not data:
                        logger.info(f"Forward {direction}: no more data, closing")
                        break
                    logger.debug(f"Forward {direction}: {len(data)} bytes")
                    logger.debug(f"  Data: {data[:200]}")
                    dst.write(data)
                    await dst.drain()
            except asyncio.TimeoutError:
                logger.warning(f"Forward {direction} timeout")
            except Exception as e:
                logger.error(f"Forward {direction} ended: {e}")
            finally:
                try:
                    dst.close()
                    await dst.wait_closed()
                except:
                    pass

        logger.info("Starting bidirectional proxy")
        await asyncio.gather(
            forward(reader, evennia_writer, "client->evennia"),
            forward(evennia_reader, writer, "evennia->client")
        )
        logger.info("Connection closed")

    except asyncio.TimeoutError:
        logger.warning("Connection timeout")
    except Exception as e:
        logger.error(f"Error handling connection: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass


async def main():
    logger.info(f"Starting WebSocket proxy on 0.0.0.0:{LISTEN_PORT}")
    logger.info(f"Forwarding to Evennia WebSocket at {EVENNIA_WS_HOST}:{EVENNIA_WS_PORT}")

    server = await asyncio.start_server(handle_client, '0.0.0.0', LISTEN_PORT)
    addr = server.sockets[0].getsockname()
    logger.info(f"Proxy listening on {addr}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())