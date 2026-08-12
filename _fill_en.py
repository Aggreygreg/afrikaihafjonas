"""Fill English .po with identity translations (msgstr = msgid)."""
import polib

po = polib.pofile('locale/en/LC_MESSAGES/django.po')
for entry in po:
    if not entry.msgstr:
        entry.msgstr = entry.msgid
po.save('locale/en/LC_MESSAGES/django.po')
print(f"English: filled {len(po)} identity translations")
