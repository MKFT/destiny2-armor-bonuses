#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本機預覽 docs/,並補上 GitHub Pages 會送、但 python3 -m http.server 不送的 charset。

為什麼需要這支:`python3 -m http.server` 對 .txt 只送「text/plain」不帶 charset,
瀏覽器只好自己猜編碼,exports 裡的中文就變亂碼。但實測真實的 GitHub Pages 送的是
「text/plain; charset=utf-8」—— 也就是說,線上其實沒問題,是本機預覽呈現了一個
線上不存在的問題。預覽會說謊比沒有預覽更糟,所以這裡把行為對齊 Pages。

(index.html 不受影響,因為它有 <meta charset>;site.json 也不受影響,
 因為 JSON 依規格一律以 UTF-8 解碼。只有 .txt 沒有任何「自帶」的編碼宣告。)

用法: python3 tools/serve.py [埠號,預設 8000]
"""
import http.server, os, sys

DOCS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs"))
TEXTY = {"text/plain", "text/html", "text/css", "text/javascript",
         "application/javascript", "application/json", "image/svg+xml"}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DOCS, **kw)
    def guess_type(self, path):
        t = super().guess_type(path)
        base = t.split(";")[0].strip()
        return f"{base}; charset=utf-8" if base in TEXTY and "charset" not in t else t
    def log_message(self, fmt, *args):
        if not args or not str(args[0]).startswith("GET"): return
        super().log_message(fmt, *args)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"預覽 {DOCS}\n  http://localhost:{port}   (Ctrl+C 結束)")
    http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
