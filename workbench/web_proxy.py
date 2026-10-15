#!/usr/bin/env python3
"""noVNC transport and a bounded Unicode clipboard bridge."""
import json
import subprocess
from pathlib import Path
from urllib.parse import urlsplit
from websockify.websocketproxy import WebSocketProxy, ProxyRequestHandler

class Handler(ProxyRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0] == '/api/status':
            path = Path('/workspace/status.json')
            body = path.read_bytes() if path.exists() else b'{"state":"starting"}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != '/api/paste' or self.headers.get('Content-Type') != 'application/json':
            self.send_error(400)
            return
        origin = self.headers.get('Origin')
        if origin and urlsplit(origin).netloc != self.headers.get('Host'):
            self.send_error(403)
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                raise ValueError('Text is too long')
            text = json.loads(self.rfile.read(size))['text']
            if not isinstance(text, str) or len(text) > 4096:
                raise ValueError('Text is too long')
            # Text is data on stdin, never part of a shell or AHK program.
            subprocess.run(['gosu', 'wineuser', 'xclip', '-selection', 'clipboard', '-in'],
                           input=text.encode('utf-8'), check=True, timeout=3)
            self.send_response(204)
            self.end_headers()
        except Exception:
            self.send_error(400, 'Clipboard could not be updated')

if __name__ == '__main__':
    WebSocketProxy(listen_host='0.0.0.0', listen_port=6080, target_host='127.0.0.1',
                   target_port=5900, web='/opt/web', RequestHandlerClass=Handler).start_server()
