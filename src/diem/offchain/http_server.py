# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

""" This module defines util functions for testing offchain inbound request processor with http server

Not recommended for production
"""

from http import server
from .http_header import X_REQUEST_ID, X_REQUEST_SENDER_ADDRESS

import logging, socket, threading, typing

logger: logging.Logger = logging.getLogger(__name__)


def start_local(
    port: int,
    process_inbound_request: typing.Callable[[str, str, bytes], typing.Tuple[int, bytes]],
) -> server.HTTPServer:
    """starts a HTTPServer on localhost with given port and callback function to process offchain inbound requests

    Warning: this is not recommended for production.

    Given process_inbound_request callable will receive:
    1. X_REQUEST_ID header value for logging purpose.
    2. DIP-5 account id for verifying JWS signature.
    3. JWS content bytes from request body.
    """

    class Handler(server.BaseHTTPRequestHandler):
        def do_POST(self):
            x_request_id = self.headers[X_REQUEST_ID]
            jws_key_address = self.headers[X_REQUEST_SENDER_ADDRESS]
            try:
                length = int(self.headers["content-length"])
                content = self.rfile.read(length)

                code, resp_body = process_inbound_request(x_request_id, jws_key_address, content)
                self.send_response(code)
                self.send_header(X_REQUEST_ID, x_request_id)
                self.end_headers()
                self.wfile.write(resp_body)
            except Exception as e:
                logger.exception(e)
                self.send_error(500, str(e))

    httpd = server.HTTPServer(("localhost", port), Handler)

    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()

    return httpd


def get_available_port() -> int:
    """get_available_port returns an available port"""

    with socket.socket() as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]
