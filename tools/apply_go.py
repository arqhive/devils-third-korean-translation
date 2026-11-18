"""돌격 명령 「고!」 → 「가!」(2026-11-18 사용자 「빼고 바꿔」).
ゴー/行け(영어 go)를 소리대로 「고!」로 옮긴 자막 5줄. 용어집 §4의 「고! 고! 고!」 줄도 같이 뺐다.

사용: python -I -X utf8 tools/apply_go.py [--apply]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
FIX = {
    'DT_Chapter_02|Subs_C055|L_006': ('고! 고! 고!', '가! 가! 가!'),
    'DT_Chapter_02|Subs_R150|L_003': ('고!', '가!'),
    'DT_Chapter_03|Subs_R020|L_012': ('좋아, 고! 고! 고!', '좋아, 가! 가! 가!'),
    'DT_Chapter_03|Subs_R040|L_008': ('고! 고! 고! 고!', '가! 가! 가! 가!'),
    'DT_Chapter_03|Subs_R140|L_019': ('고! 고! 고!', '가! 가! 가!'),
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
            assert d[k] == FIX[k][0], (k, d[k])
            hit[k] = f
            print(f, k, '|', d[k], '→', FIX[k][1])
        if ks:
            files.append((p, d, ks))
    assert set(hit) == set(FIX), set(FIX) - set(hit)
    if '--apply' not in sys.argv:
        return
    for p, d, ks in files:
        for k in ks:
            d[k] = FIX[k][1]
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('반영', len(hit))


if __name__ == '__main__':
    main()
