"""수집품 문서 제목 안의 겹친 따옴표 빼기(2026-11-18 사용자: 작은따옴표 안에 큰따옴표가 맞냐 → 1번 「안쪽 따옴표 빼기」).
규정은 바깥 큰따옴표·안쪽 작은따옴표라 ‘…“…”…’ 꼴은 맞지 않음. 해당 3줄의 제목 줄에서만 “ ” 를 뺀다.

사용: python -I -X utf8 tools/apply_quote_titles.py [--apply]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
PAT = re.compile(r'‘[^’]*“[^’]*’')


def fix(v):
    return PAT.sub(lambda m: m.group(0).replace('“', '').replace('”', ''), v)


def main():
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    want = {k: (v, fix(v)) for k, v in ko.items() if PAT.search(v)}
    assert len(want) == 3, sorted(want)
    for k, (b, a) in want.items():
        print(k, '|', PAT.search(b).group(0), '→', a.split('\n')[0])
    if '--apply' not in sys.argv:
        return
    hit = set()
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        chg = False
        for key in d:
            if key in want:
                assert d[key] == want[key][0], key
                d[key] = want[key][1]
                hit.add(key)
                chg = True
        if chg:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert hit == set(want)
    print('반영', len(hit))


if __name__ == '__main__':
    main()
