#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply the HSK1 QA patches to review_queue_raw.json.

Usage:
    python3 apply_patches.py --dry-run          # report only
    python3 apply_patches.py --out fixed.json   # write result

Patches are applied in this order (later wins):
    1. patch_format.json      punctuation normalisation
    2. patch_pinyin.json      systematic pinyin corrections
    3. patch_content.json     linguistic corrections (zh / es / pos / meaning)
    4. patch_new_senses.json  whole new sense objects, appended
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, os.pardir, 'review_queue_raw.json')

SPARSE = ['patch_format.json', 'patch_pinyin.json', 'patch_content.json']
NEW    = 'patch_new_senses.json'


def load(name):
    p = os.path.join(HERE, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--out', default=os.path.join(HERE, 'review_queue_fixed.json'))
    a = ap.parse_args()

    data = json.load(open(SRC, encoding='utf-8'))
    index = {(e['no'], e['sense_index']): e for e in data}
    stats = {'fields': 0, 'examples': 0, 'added': 0, 'misses': []}

    for name in SPARSE:
        for patch in load(name):
            key = (patch['no'], patch['sense_index'])
            target = index.get(key)
            if target is None:
                stats['misses'].append((name, key)); continue
            for field, value in patch.items():
                if field in ('no', 'sense_index'):
                    continue
                if field == 'examples':
                    for i, changed in value.items():
                        i = int(i)
                        if i >= len(target['examples']):
                            stats['misses'].append((name, key, i)); continue
                        for k, v in changed.items():
                            if target['examples'][i].get(k) != v:
                                target['examples'][i][k] = v
                                stats['examples'] += 1
                else:
                    if target.get(field) != value:
                        target[field] = value
                        stats['fields'] += 1

    for sense in load(NEW):
        key = (sense['no'], sense['sense_index'])
        if key in index:
            stats['misses'].append((NEW, key, 'already exists')); continue
        data.append(sense); index[key] = sense; stats['added'] += 1

    print(f"field changes:   {stats['fields']}")
    print(f"example changes: {stats['examples']}")
    print(f"senses added:    {stats['added']}")
    if stats['misses']:
        print('MISSES:', *stats['misses'], sep='\n  ')
        return 1
    if not a.dry_run:
        json.dump(data, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('wrote', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
