"""자막 대사를 영어 자막 기준으로 다시 번역하기 위한 묶음 만들기(2026-11-18 사용자 지시, 범위: 자막 대사만).

입력: work/translation/src/*.json(원문·영어·화자·줄 수), work/translation/ko.json(지금 번역),
      work/review2/locked.json(사용자가 정한 줄)
출력: work/review3/src/<묶음>.json — 영어가 있는 자막 줄만(장면 순서 그대로). 원문이 들어 있어 커밋 금지.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TR = os.path.join(ROOT, 'work', 'translation')
OUT = os.path.join(ROOT, 'work', 'review3', 'src')

GROUPS = [
    ('S1_ch00-02', ('DT_Chapter_00', 'DT_Chapter_01', 'DT_Chapter_02')),
    ('S2_ch03', ('DT_Chapter_03', 'DT_Chapter_03_Mg1', 'DT_Chapter_03_Mg2')),
    ('S3_ch04', ('DT_Chapter_04', 'DT_Chapter_04_Mg1', 'DT_Chapter_04_Mg2')),
    ('S4_ch05-06', ('DT_Chapter_05', 'DT_Chapter_05_Mg1', 'DT_Chapter_06')),
    ('S5_ch07', ('DT_Chapter_07', 'DT_Chapter_07_Mg1')),
    ('S6_ch08', ('DT_Chapter_08', 'DT_Chapter_08_Mg1', 'DT_Chapter_08_Mg2')),
    ('S7_ch09', ('DT_Chapter_09',)),
]


def main():
    ko = json.load(open(os.path.join(TR, 'ko.json'), encoding='utf-8'))
    locked = json.load(open(os.path.join(ROOT, 'work', 'review2', 'locked.json'), encoding='utf-8'))
    rows = []
    for f in sorted(os.listdir(os.path.join(TR, 'src'))):
        if f.endswith('.json'):
            rows += json.load(open(os.path.join(TR, 'src', f), encoding='utf-8'))
    subs = [r for r in rows if '|Subs_' in r['key'] and r['key'] in ko]
    os.makedirs(OUT, exist_ok=True)
    total = skipped = 0
    for name, files in GROUPS:
        items = []
        for r in subs:
            if r['file'] not in files:
                continue
            en = (r.get('en') or '').strip()
            if not en or en == r['jp']:
                skipped += 1
                continue
            items.append({
                'key': r['key'], 'section': r['section'], 'speaker': r.get('speaker'),
                'lines': r.get('lines'), 'jp': r['jp'], 'en': r['en'], 'ko_now': ko[r['key']],
                'locked': r['key'] in locked,
            })
        json.dump(items, open(os.path.join(OUT, name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(name, len(items), '고정 줄', sum(i['locked'] for i in items))
        total += len(items)
    print('합계', total, '영어 없어 뺀 줄', skipped, '자막 전체', len(subs))


if __name__ == '__main__':
    main()
