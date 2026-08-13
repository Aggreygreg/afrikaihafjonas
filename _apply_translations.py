"""
Apply HU + DE translations from JSON files to .po files.
Processes multiple JSON files per language (rounds 1+2).
Run: python _apply_translations.py
"""
import json
import polib
import os

LANG_FILES = {
    'hu': ['locale/_hu_translations.json', 'locale/_hu_translations2.json'],
    'de': ['locale/_de_translations.json', 'locale/_de_translations2.json'],
}

for lang, json_files in LANG_FILES.items():
    # Merge all JSON files for this language
    translations = {}
    for jf in json_files:
        if os.path.exists(jf):
            with open(jf, encoding='utf-8') as f:
                translations.update(json.load(f))

    po_path = f'locale/{lang}/LC_MESSAGES/django.po'
    po = polib.pofile(po_path)

    filled = 0
    for entry in po.untranslated_entries():
        if entry.msgid in translations:
            entry.msgstr = translations[entry.msgid]
            filled += 1

    po.save(po_path)
    remaining = len(po.untranslated_entries())

    print(f"\n{'='*60}")
    print(f"  {lang.upper()}: filled {filled} new translations")
    print(f"  Total: {len(po)}, Translated: {len(po.translated_entries())}, Remaining: {remaining}")

    if remaining:
        print(f"  ⚠ Still untranslated:")
        for e in po.untranslated_entries():
            print(f"    - {e.msgid[:80]}")

print("\n\nNext: python _compile_mo.py")
