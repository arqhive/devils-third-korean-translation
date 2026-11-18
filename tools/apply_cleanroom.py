"""「소탕 하나는」 → 「방 청소 하나는」(2026-11-18 사용자 지시). 6장 R110 L_002 한 줄.

사용: python -I -X utf8 tools/apply_cleanroom.py [--apply]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
FIX = {
    'DT_Chapter_06|Subs_R110|L_002': ('젠장! 저 친구, 소탕 하나는 끝내주는군.',
                                      '젠장! 저 친구, 방 청소 하나는 끝내주는군.'),
}


def main():
    hit = {}
    files = []
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        ks = [k for k in d if k in FIX]
        for k in ks:
            if d[k] == FIX[k][1]:
                print(f, k, '이미 반영')
                continue
            assert d[k] == FIX[k][0], (k, d[k])
            hit[k] = f
            print(f, k, '|', repr(d[k]), '→', repr(FIX[k][1]))
        if ks:
            files.append((p, d, ks))
    if '--apply' not in sys.argv:
        return
    for p, d, ks in files:
        for k in ks:
            d[k] = FIX[k][1]
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('반영', len(hit))


if __name__ == '__main__':
    main()
