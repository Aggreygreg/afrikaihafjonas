"""Extract just the HU dict from _fill_translations.py."""
lines = open('_fill_translations.py', encoding='utf-8').readlines()
de_start = None
for i, l in enumerate(lines):
    if 'DE = {' in l:
        de_start = i
        break
if de_start:
    kept = lines[:de_start]
    kept.append('}\n')
    open('_fill_translations.py', 'w', encoding='utf-8').writelines(kept)
    print(f'Kept {len(kept)} lines (HU dict only)')
else:
    print('DE not found - file may already be clean')
