#!/usr/bin/env python3
"""Loopback-only emulator server. Optional single firmware file, no directory dumps."""
import argparse
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]/'emulator'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8766);p.add_argument('--firmware',type=Path);a=p.parse_args()
 firmware=a.firmware.resolve() if a.firmware else None
 if firmware and (not firmware.is_file() or firmware.stat().st_size!=4096):p.error('Firmware must be a4096-byte file')
 class Handler(SimpleHTTPRequestHandler):
  extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript'}
  def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
  def list_directory(self,path):self.send_error(403);return None
  def do_GET(self):
   if urlsplit(self.path).path=='/lab-firmware.bin':
    if not firmware:self.send_error(404);return
    data=firmware.read_bytes();self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
   else:super().do_GET()
  def end_headers(self):
   self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'");super().end_headers()
 print(f'H-6CS emulator: http://127.0.0.1:{a.port}',flush=True)
 ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
if __name__=='__main__':main()
