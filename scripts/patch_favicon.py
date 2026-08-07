from pathlib import Path
import re

index = Path('index.html')
data_file = Path('favicon-data.txt')

html = index.read_text(encoding='utf-8')
data_uri = data_file.read_text(encoding='utf-8').strip()
link = f'<link rel="icon" type="image/png" sizes="32x32" href="{data_uri}"/>'

# Replace an existing embedded favicon or insert immediately after <title>.
if re.search(r'<link rel="icon"[^>]*>', html):
    html = re.sub(r'<link rel="icon"[^>]*>', link, html, count=1)
else:
    html = html.replace('</title>', '</title>\n' + link, 1)

# Match the approved dark radar artwork in browser chrome where supported.
if 'name="theme-color"' not in html:
    html = html.replace('</title>', '</title>\n<meta name="theme-color" content="#07110c"/>', 1)

index.write_text(html, encoding='utf-8')
print('Exact Momentum Radar favicon installed')
