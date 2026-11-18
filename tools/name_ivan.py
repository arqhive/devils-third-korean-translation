"""이반 → 아이반 되돌리기(2026-11-18 사용자: 「영어 음성도 아이반, 아이반 더 테러블로 나옴」).
「이반 더 테러블」도 「아이반 더 테러블」로. 받침 같음(ㄴ) → 조사 그대로.
앞에 한글이 붙은 「이반」(다른 낱말 속)은 건드리지 않는다(조회 때 0건 확인).

사용: python -I -X utf8 tools/name_ivan.py [--apply]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
PAT = re.compile(r'(?<![가-힣])이반')


def main():
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    want = {k: (v, PAT.sub('아이반', v)) for k, v in ko.items() if PAT.search(v)}
    print('바뀌는 줄', len(want), '곳', sum(len(PAT.findall(v)) for v, _ in want.values()))
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
