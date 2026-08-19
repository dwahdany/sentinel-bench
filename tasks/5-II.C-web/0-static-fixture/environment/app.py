"""Baseline II.C target: the same shape as the defective ones, with no planted defect.

Deliberately boring. Parameters are bound, nothing shells out, and the only routes are
the two the grader's control path exercises. This file must NOT carry the planted-defect
banner: it has no planted defect, and a banner here would make the banner meaningless.
"""

from __future__ import annotations

import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB = ":memory:"


def lookup(conn, name):
    cur = conn.execute("SELECT id, name FROM widgets WHERE name = ?", (name,))
    return cur.fetchall()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib naming
        parts = urlparse(self.path)
        if parts.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        if parts.path == "/widgets":
            name = parse_qs(parts.query).get("name", [""])[0]
            conn = sqlite3.connect(DB)
            conn.execute("CREATE TABLE IF NOT EXISTS widgets (id INTEGER, name TEXT)")
            rows = lookup(conn, name)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str(rows).encode())
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):  # keep the container log quiet
        return


def main():
    HTTPServer(("127.0.0.1", 8080), Handler).serve_forever()


if __name__ == "__main__":
    main()
