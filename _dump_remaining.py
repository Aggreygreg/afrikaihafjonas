"""Dump remaining untranslated strings."""
import polib
import json

for lang in ('hu', 'de'):
    po = polib.pofile(f'locale/{lang}/LC_MESSAGES/django.po')
    untranslated = [e.msgid for e in po.untranslated_entries()]
    print(f"\n=== {lang.upper()}: {len(untranslated)} untranslated ===")
    for i, s in enumerate(untranslated, 1):
        print(f'{i}. {repr(s)}')
