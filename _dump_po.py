"""Dump translated and untranslated msgids for analysis."""
import polib

for lang in ('hu',):
    po = polib.pofile(f'locale/{lang}/LC_MESSAGES/django.po')
    print(f'=== {lang.upper()} TRANSLATED ({len(po.translated_entries())}) ===')
    for e in po.translated_entries():
        print(f'  {repr(e.msgid)} => {repr(e.msgstr)}')
    print(f'\n=== {lang.upper()} UNTRANSLATED ({len(po.untranslated_entries())}) ===')
    for e in po.untranslated_entries():
        print(f'  {repr(e.msgid)}')
