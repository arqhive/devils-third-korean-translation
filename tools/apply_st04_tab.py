"""수집품 ST_04 「BRAAT 내비 쿠폰도」 줄 앞 탭 빼기(2026-11-18 사용자 「저 (공백) 지워」). 한 곳.

사용: python -I -X utf8 tools/apply_st04_tab.py [--apply]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
KEY = 'DT_CollectItems|Descriptions|ST_04'
OLD = '\n\tBRAAT 내비 쿠폰도'
NEW = '\nBRAAT 내비 쿠폰도'


def main():
    files = []
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        if KEY in d:
            print(f, KEY, '바꿀 곳', d[KEY].count(OLD), '이 줄 탭 수', d[KEY].count('\t'))
            files.append((p, d))
    assert len(files) == 1 and files[0][1][KEY].count(OLD) == 1
    if '--apply' not in sys.argv:
        return
    p, d = files[0]
    d[KEY] = d[KEY].replace(OLD, NEW)
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('반영 1')


if __name__ == '__main__':
    main()
