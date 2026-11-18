"""스텔라 「비오프레파라트」 → 「바이오프레파라트」(2026-11-18 사용자 지시). 4장 C120 L_005 한 줄.

사용: python -I -X utf8 tools/apply_biopreparat.py [--apply]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
FIX = {
    'DT_Chapter_04|Subs_C120|L_005': ('\n들어갔어!\n소련 정부가 비오프레파라트에 보낸 보고서 같아…',
                                      '\n들어갔어!\n소련 정부가 바이오프레파라트에 보낸 보고서 같아…'),
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
