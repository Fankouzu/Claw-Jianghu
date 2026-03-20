#!/usr/bin/env python3
"""
Simple WebSocket proxy for Evennia.
Receives WSS connections and forwards to Evennia's WebSocket server.
Also handles HTTP health checks for Railway.
"""
import asyncio
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EVENNIA_WS_HOST = "127.0.0.1"
EVENNIA_WS_PORT = 4002
LISTEN_PORT = int(os.environ.get("PORT", 8080))


class WebSocketProxy:
    def __init__(self):
        self.connections = 0

    async def handle_client(self, reader, writer):
        """Handle incoming connection - could be WebSocket or HTTP health check."""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {client_addr}")

        try:
            # Read the first few bytes to determine if this is HTTP
            data = await asyncio.wait_for(reader.read(1024), timeout=5)

            if not data:
                logger.warning("No data received, closing connection")
                writer.close()
                await writer.wait_closed()
                return

            # Check if this is an HTTP request (starts with method like GET, POST)
            request_line = data.decode('utf-8', errors='ignore').split('\r\n')[0]

            if request_line.startswith(('GET ', 'POST ', 'HEAD ')):
                # This is an HTTP request - handle it
                await self.handle_http(reader, writer, data, request_line)
            else:
                # This might be a WebSocket connection
                # For now, close it as we expect WebSocket upgrade via HTTP
                logger.warning(f"Non-HTTP connection attempt: {request_line[:50]}")
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\nWebSocket upgrade required")
                await writer.drain()
                writer.close()
                await writer.wait_closed()

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

    async def handle_http(self, reader, writer, initial_data, request_line):
        """Handle HTTP request - could be WebSocket upgrade or health check."""
        try:
            # Parse the request
            parts = request_line.split(' ')
            method = parts[0] if parts else ''
            path = parts[1] if len(parts) > 1 else '/'

            logger.info(f"HTTP request: {method} {path}")

            # Read more data if needed
            try:
                more_data = await asyncio.wait_for(reader.read(4096), timeout=2)
                initial_data += more_data
            except asyncio.TimeoutError:
                pass

            request_str = initial_data.decode('utf-8', errors='ignore')

            # Check for WebSocket upgrade
            headers = {}
            for line in request_str.split('\r\n')[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            # Health check endpoint
            if path == '/health':
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
                writer.write(response.encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                return

            # WebSocket upgrade
            if headers.get('upgrade', '').lower() == 'websocket':
                await self.handle_websocket_upgrade(reader, writer, request_str, headers)
                return

            # Regular HTTP request - return info
            response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            response += json.dumps({
                "service": "Evennia WebSocket Proxy",
                "status": "running",
                "evennia_host": EVENNIA_WS_HOST,
                "evennia_port": EVENNIA_WS_PORT
            })
            writer.write(response.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        except Exception as e:
            logger.error(f"Error handling HTTP: {e}")
            try:
                writer.write(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def handle_websocket_upgrade(self, reader, writer, request_str, headers):
        """Handle WebSocket upgrade and proxy to Evennia."""
        try:
            # Connect to Evennia's WebSocket server
            logger.info("Connecting to Evennia WebSocket...")

            evennia_reader, evennia_writer = await asyncio.wait_for(
                asyncio.open_connection(EVENNIA_WS_HOST, EVENNIA_WS_PORT),
                timeout=10
            )
            logger.info("Connected to Evennia WebSocket")

            # Forward the upgrade request to Evennia
            evennia_writer.write(request_str.encode())
            await evennia_writer.drain()

            # Read Evennia's response
            response = await asyncio.wait_for(evennia_reader.read(4096), timeout=10)
            logger.info(f"Evennia response: {response[:100]}")

            # Forward response to client
            writer.write(response)
            await writer.drain()

            # Now proxy bidirectionally
            self.connections += 1
            logger.info(f"Active connections: {self.connections}")

            async def forward_to_evennia():
                try:
                    while True:
                        data = await reader.read(4096)
                        if not data:
                            break
                        evennia_writer.write(data)
                        await evennia_writer.drain()
                except Exception as e:
                    logger.debug(f"Forward to Evennia ended: {e}")
                finally:
                    try:
                        evennia_writer.close()
                        await evennia_writer.wait_closed()
                    except:
                        pass

            async def forward_to_client():
                try:
                    while True:
                        data = await evennia_reader.read(4096)
                        if not data:
                            break
                        writer.write(data)
                        await writer.drain()
                except Exception as e:
                    logger.debug(f"Forward to client ended: {e}")
                finally:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except:
                        pass

            await asyncio.gather(forward_to_evennia(), forward_to_client())
            self.connections -= 1
            logger.info(f"Connection closed. Active: {self.connections}")

        except Exception as e:
            logger.error(f"WebSocket upgrade failed: {e}")
            response = "HTTP/1.1 502 Bad Gateway\r\n\r\nFailed to connect to game server"
            try:
                writer.write(response.encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def start(self):
        """Start the proxy server."""
        server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            LISTEN_PORT
        )
        addr = server.sockets[0].getsockname()
        logger.info(f"WebSocket proxy listening on {addr}")
        logger.info(f"Forwarding to Evennia at {EVENNIA_WS_HOST}:{EVENNIA_WS_PORT}")

        async with server:
            await server.serve_forever()


async def main():
    proxy = WebSocketProxy()
    await proxy.start()


if __name__ == "__main__":
    asyncio.run(main())