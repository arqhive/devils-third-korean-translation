"""아이반·빅 마우스 말끝 2차(2026-11-18 사용자 지정, 아이반·빅 마우스 대사표에서 짚은 줄만).
「알았어.」는 아이반 줄 2개(4장 C020 L_005 밥에게, 8장 C040 L_006 스텔라에게)만. 스텔라 「알았어.」 6줄은 그대로.
「보이지 않느냐?」는 빅 마우스 줄만(샤하 3장 C070 L_006 은 그대로).
사용: python -I -X utf8 tools/apply_ivan_tone2.py [--apply]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
FIX = {
    'DT_Chapter_04|Subs_C020|L_005': ('알았어.', '그러지.'),
    'DT_Chapter_08|Subs_C040|L_006': ('알았어.', '그러지.'),
    'DT_Chapter_08_Mg1|Subs_Set03|L_003': ('미사일이 온다.', '미사일인가.'),
    'DT_Chapter_02|Subs_C100|L_002': ('빌러 왔느냐?', '빌러 왔는가?'),
    'DT_Chapter_02|Subs_C120|L_002': ('보이지 않느냐?', '보이지 않는가?'),
}


def main():
    hit = {}
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        ks = [k for k in d if k in FIX]
        for k in ks:
            a, b = FIX[k]
            hit[k] = f
            if a not in d[k] and b in d[k]:
                print(f, k, '| 이미 반영됨')
                continue
            assert d[k].count(a) == 1, (k, d[k])
            print(f, k, '|', d[k].replace('\n', '/'), '→', d[k].replace(a, b).replace('\n', '/'))
            hit[k] = f
            if '--apply' in sys.argv:
                d[k] = d[k].replace(a, b)
        if ks and '--apply' in sys.argv:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert set(hit) == set(FIX), set(FIX) - set(hit)
    print('반영' if '--apply' in sys.argv else '조회', len(hit))


if __name__ == '__main__':
    main()
