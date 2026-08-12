"""Compile .po files to .mo using polib (no GNU gettext needed)."""
import polib
import os

for lang in ('hu', 'de', 'en'):
    po_path = f'locale/{lang}/LC_MESSAGES/django.po'
    if not os.path.exists(po_path):
        print(f"  SKIP {po_path} — not found")
        continue
    po = polib.pofile(po_path)
    mo_path = po_path.replace('.po', '.mo')
    po.save(mo_path)
    translated = len(po.translated_entries())
    total = len(po)
    print(f"  Compiled {mo_path}: {translated}/{total} translated")
