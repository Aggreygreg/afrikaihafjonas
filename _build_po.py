"""
Build fresh .po files for HU/EN/DE from extracted template/Python strings.

Without GNU gettext (not installed on this Windows machine), we use polib
to create properly formatted .po files directly.

Run: python _build_po.py
"""
import os
import re
from collections import OrderedDict
import polib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── String extraction ───────────────────────────────────────────
TRANS_PATTERNS = [
    (re.compile(r"""{%\s*trans\s+["']([^"']+)["']"""), 'template'),
    (re.compile(r"""_\(\s*["']([^"']+)["']"""), 'python'),
    (re.compile(r"""gettext\(\s*["']([^"']+)["']"""), 'python'),
]
SKIP_DIRS = {'.venv', '__pycache__', 'node_modules', '.git', 'mediafiles',
             'staticfiles', 'locale', 'theme', '.qwenpaw'}
TEMPLATE_EXTS = {'.html', '.txt'}
PYTHON_EXTS = {'.py'}

strings = OrderedDict()
occurrences = {}

for root, dirs, files in os.walk(BASE_DIR):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for fname in files:
        fpath = os.path.join(root, fname)
        ext = os.path.splitext(fname)[1]
        if ext not in TEMPLATE_EXTS and ext not in PYTHON_EXTS:
            continue
        try:
            with open(fpath, encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            continue
        relpath = os.path.relpath(fpath, BASE_DIR).replace('\\', '/')
        for pattern, _ in TRANS_PATTERNS:
            for match in pattern.finditer(content):
                s = match.group(1).strip()
                if not s:
                    continue
                if s not in strings:
                    strings[s] = True
                    occurrences[s] = []
                occurrences[s].append(relpath)

print(f"Extracted {len(strings)} unique translatable strings")

# ── Load existing translations ──────────────────────────────────
existing = {}
for lang in ('hu', 'de', 'en'):
    po_path = f'locale/{lang}/LC_MESSAGES/django.po'
    if os.path.exists(po_path):
        old_po = polib.pofile(po_path)
        existing[lang] = {e.msgid: e.msgstr for e in old_po if e.msgstr}
        print(f"  Loaded {len(existing[lang])} existing {lang} translations")
    else:
        existing[lang] = {}

# ── Build .po files ─────────────────────────────────────────────
for lang in ('hu', 'de', 'en'):
    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': 'Afrikai Hajfonas 1.0',
        'Report-Msgid-Bugs-To': '',
        'POT-Creation-Date': '2026-08-12 00:00+0000',
        'PO-Revision-Date': '2026-08-12 00:00+0000',
        'Last-Translator': 'HICLAW Manager',
        'Language-Team': f'{lang} <afrikai@hajfonas.hu>',
        'Language': lang,
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }

    for msgid in strings:
        entry = polib.POEntry(
            msgid=msgid,
            msgstr=existing[lang].get(msgid, ''),
            occurrences=[(occ, '') for occ in occurrences[msgid][:3]],
        )
        po.append(entry)

    po_path = f'locale/{lang}/LC_MESSAGES/django.po'
    po.save(po_path)
    untranslated = len([e for e in po if not e.msgstr])
    print(f"  Wrote {po_path}: {len(po)} entries ({untranslated} untranslated)")

print("\nDone. Now fill in translations and run _compile_mo.py")
