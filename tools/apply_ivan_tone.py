"""아이반 말끝 5줄(2026-11-18 사용자 지정, 그 줄만).
사용: python -I -X utf8 tools/apply_ivan_tone.py [--apply]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
FIX = [
    ('그 애들이 테러리스트였냐?', '그 애들이 테러리스트였나?'),
    ('비컨탄을 박아 뒀다.', '비컨탄을 박아 뒀어.'),
    ('녀석들 거점을 찾았다. 하늘에서 칠 수 있어?', '녀석들 거점을 찾았다. 하늘에서 칠 수 있나?'),
    ('아는 건 그게 다야?', '아는 건 그게 다인가?'),
    ('혼자 걸을 수 있겠어?', '혼자 걸을 수 있겠나?'),
]


def main():
    hits = []
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        d = json.load(open(os.path.join(OD, f), encoding='utf-8'))
        for k, v in d.items():
            for a, b in FIX:
                if a in v:
                    hits.append((f, k, a, b, v))
    for h in hits:
        print(h[0], h[1], '|', h[4].replace('\n', '/'))
    found = sorted({h[2] for h in hits})
    assert len(hits) == len(FIX) and len(found) == len(FIX), (len(hits), found)
    if '--apply' not in sys.argv:
        return
    for f in sorted({h[0] for h in hits}):
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        for hf, k, a, b, _ in hits:
            if hf == f:
                d[k] = d[k].replace(a, b)
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('반영', len(hits))


if __name__ == '__main__':
    main()
