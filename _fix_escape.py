"""Fix the backslash-quote issue in _fill_translations.py"""
content = open('_fill_translations.py', encoding='utf-8').read()

# The problem entry: 'No popular services have been selected yet. Mark some as \'
# In Python source, \' inside single quotes is an escaped quote, so the string
# never terminates. We need to use \\ to represent a literal backslash.
# Replace the problematic entries:
content = content.replace(
    "Mark some as \\': ",
    'Mark some as \\\\\': ',
)

# Write back
open('_fill_translations.py', 'w', encoding='utf-8').write(content)
print("Fixed backslash escaping")
