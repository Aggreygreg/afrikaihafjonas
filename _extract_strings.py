"""
Extract all translatable strings from templates and Python code.
Outputs a deduplicated list for translation work.
"""
import os
import re
from collections import OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Patterns to find translation strings
TRANS_PATTERNS = [
    # {% trans "..." %} or {% trans '...' %}
    (re.compile(r"""{%\s*trans\s+["']([^"']+)["']"""), 'template'),
    # {% blocktrans %}...{% endblocktrans %}
    (re.compile(r"""{%\s*blocktrans[^%]*%}(.*?){%\s*endblocktrans\s*%}""", re.DOTALL), 'blocktrans'),
    # _("...") or _('...')  in Python
    (re.compile(r"""_\(\s*["']([^"']+)["']"""), 'python'),
    # gettext("...") or gettext('...')
    (re.compile(r"""gettext\(\s*["']([^"']+)["']"""), 'python'),
]

SKIP_DIRS = {'.venv', '__pycache__', 'node_modules', '.git', 'mediafiles',
             'staticfiles', 'locale', 'theme', '.qwenpaw'}
TEMPLATE_EXTS = {'.html', '.txt'}
PYTHON_EXTS = {'.py'}

strings = OrderedDict()

for root, dirs, files in os.walk(BASE_DIR):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for fname in files:
        fpath = os.path.join(root, fname)
        ext = os.path.splitext(fname)[1]
        relpath = os.path.relpath(fpath, BASE_DIR)

        if ext not in TEMPLATE_EXTS and ext not in PYTHON_EXTS:
            continue

        try:
            with open(fpath, encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            continue

        for pattern, ptype in TRANS_PATTERNS:
            for match in pattern.finditer(content):
                s = match.group(1).strip()
                if s and s not in strings:
                    strings[s] = {'file': relpath, 'type': ptype}

print(f"Total unique translatable strings: {len(strings)}")
print()
for i, (s, info) in enumerate(strings.items(), 1):
    # Truncate long strings for display
    display = s[:80] + '...' if len(s) > 80 else s
    print(f"{i:3d}. [{display}]")
