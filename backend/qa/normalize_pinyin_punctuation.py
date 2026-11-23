#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OPTIONAL: normalise punctuation inside the `pinyin` field only.

The source mixes CJK punctuation (。？，“”) with Latin punctuation inside romanised
text, and inserts a space before it ("... nǎ lǐ ?"). Pinyin is a Latin-script
transcription, so it should carry Latin punctuation, attached to the preceding
word.  This script rewrites only `examples[].pinyin`; it never touches `zh`.

    python3 normalize_pinyin_punctuation.py in.json out.json
"""
import json, re, sys

MAP = {'。': '.', '，': ',', '？': '?', '！': '!', '：': ':', '、': ',',
       '；': ';', '—': '-'}
OPEN, CLOSE = '\u201c', '\u201d'


def fix(py):
    py = py.replace(OPEN, '\x01').replace(CLOSE, '\x02').replace('"', '\x01')
    for a, b in MAP.items():
        py = py.replace(a, b)
    py = re.sub(r'\s+([,.?!:;])', r'\1', py)        # no space before punctuation
    py = re.sub(r'([,.?!:;])(?=[^\s\x02])', r'\1 ', py)  # one space after
    py = re.sub(r'\x01\s*', '"', py)                # no space after opening quote
    py = re.sub(r'\s*\x02', '"', py)                # no space before closing quote
    return re.sub(r'\s{2,}', ' ', py).strip()


def main(src, dst):
    data = json.load(open(src, encoding='utf-8'))
    n = 0
    for e in data:
        for ex in e['examples']:
            new = fix(ex['pinyin'])
            if new != ex['pinyin']:
                ex['pinyin'] = new
                n += 1
    json.dump(data, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'normalised {n} pinyin strings -> {dst}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
