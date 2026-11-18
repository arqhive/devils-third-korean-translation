"""「~숏」 → 「~샷」(2026-11-18 사용자 지시 「샷건을 숏건이라곤 안 쓰잖아」, 대조표 7줄 승인).

사용: python -I -X utf8 tools/apply_shot.py          → 조회만
      python -I -X utf8 tools/apply_shot.py --apply  → 덩어리 번역(work/translation/out)에 넣음
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))

KEYS = [
    'DT_UI_Labels|Param_Labels|HeadShot',
    'DT_UI_Labels|Param_Labels|LongShot',
    'DT_UI_Labels|Param_Labels|OneShotOneKill',
    'DT_Tips|Single|Enemy_11',
    'DT_Tips|Single|Mission_04',
    'DT_Tips|Single|Mission_05',
    'DT_Tips|Single|Mission_06',
]
PAIRS = [('헤드숏', '헤드샷'), ('롱숏', '롱샷'), ('1숏', '1샷')]


def main():
    found = sorted(k for k, v in ko.items() if '숏' in v)
    assert found == sorted(KEYS), found  # 승인 표와 개수·키가 같을 때만
    want = {}
    for k in KEYS:
        after = ko[k]
        for a, b in PAIRS:
            after = after.replace(a, b)
        assert '숏' not in after, k
        want[k] = (ko[k], after)
        print(k, '|', ko[k].replace('\n', '/'), '→', after.replace('\n', '/'))
    if '--apply' not in sys.argv:
        return
    hit = set()
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        ch = False
        for key in d:
            if key in want:
                assert d[key] == want[key][0], key
                d[key] = want[key][1]
                hit.add(key)
                ch = True
        if ch:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert hit == set(want)
    print('반영', len(hit))


if __name__ == '__main__':
    main()
