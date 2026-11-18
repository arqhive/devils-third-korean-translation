"""メレーショット(Melee Shot, ZL+X 로 근접 무기를 던지는 동작) 「근접 사격」 → 「무기 투척」
(2026-11-18 사용자: 「던지는 건데 사격이라는 문구가 나와」, 「무기 투척」 선택). 받침 같음(ㄱ) → 조사 그대로.

사용: python -I -X utf8 tools/apply_melee.py [--apply]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
KEYS = ['DT_UI_Labels|Param_Labels|ThrowingKnife', 'DT_UI_Tutorial|Subtitles|locMessages[68]',
        'DT_Tips|Multi_Single|Action_05', 'DT_Tips|Single|Mission_09']


def main():
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    found = sorted(k for k, v in ko.items() if '근접 사격' in v)
    assert found == sorted(KEYS), found
    want = {k: (ko[k], ko[k].replace('근접 사격', '무기 투척')) for k in KEYS}
    for k, (b, a) in want.items():
        print(k, '|', b.replace('\n', '/'), '→', a.replace('\n', '/'))
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
