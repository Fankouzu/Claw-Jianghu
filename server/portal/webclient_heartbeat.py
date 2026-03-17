"""
Custom WebSocket protocol with heartbeat support for Railway deployment.

This module provides a WebSocket client with automatic ping/pong heartbeat mechanism
to prevent Railway's proxy from closing idle connections.
"""
from twisted.internet import reactor
from evennia.server.portal.webclient import WebSocketClient
from evennia.utils import logger


class WebSocketClientWithHeartbeat(WebSocketClient):
    """
    WebSocket client with automatic WebSocket-level ping to keep connections alive.

    Railway's proxy closes idle connections after ~60 seconds of inactivity.
    This sends periodic WebSocket ping frames to prevent disconnection.

    WebSocket ping/pong is a protocol-level mechanism that doesn't require
    client-side JavaScript handling - the browser automatically responds with pong.
    """

    # Heartbeat interval in seconds (send ping every 30 seconds)
    # Railway typically has a 60-second idle timeout
    HEARTBEAT_INTERVAL = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._heartbeat_call = None

    def onOpen(self):
        """Called when WebSocket connection is established."""
        super().onOpen()
        self._start_heartbeat()

    def onClose(self, wasClean, code=None, reason=None):
        """Called when WebSocket connection is closed."""
        self._stop_heartbeat()
        super().onClose(wasClean, code, reason)

    def _start_heartbeat(self):
        """Start the heartbeat loop."""
        if self._heartbeat_call is None:
            self._heartbeat_call = reactor.callLater(
                self.HEARTBEAT_INTERVAL, self._send_heartbeat
            )

    def _stop_heartbeat(self):
        """Stop the heartbeat loop."""
        if self._heartbeat_call is not None:
            self._heartbeat_call.cancel()
            self._heartbeat_call = None

    def _send_heartbeat(self):
        """Send a WebSocket ping frame and schedule the next heartbeat."""
        if self.state == self.STATE_OPEN:
            try:
                # Send WebSocket protocol-level ping
                # Browser will automatically respond with pong
                self.sendPing()
            except Exception as e:
                logger.log_trace(e)

        # Schedule next heartbeat
        self._heartbeat_call = reactor.callLater(
            self.HEARTBEAT_INTERVAL, self._send_heartbeat
        )