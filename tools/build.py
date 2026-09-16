"""Build index.html (the page GitHub Pages serves) from src/diagram-table.html.

The source is written as an *Artifact body*: no doctype, no <html>/<head>/<body>, because
the claude.ai runtime supplies those at publish time. Served raw over HTTP that would
render in quirks mode, so this wraps it in the same skeleton the runtime uses.

    py tools/build.py
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKELETON = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;font:14px system-ui,sans-serif;background:#fafaf9}
img{max-width:100%}
[hidden]{display:none!important}
</style>
</head>
<body>
@@BODY@@
</body>
</html>
"""

body = io.open(os.path.join(ROOT, 'src', 'diagram-table.html'), encoding='utf-8').read()
io.open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(
    SKELETON.replace('@@BODY@@', body))
print('index.html written from src/diagram-table.html (%d chars)' % len(body))
