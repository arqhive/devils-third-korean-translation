"""모든 번역을 영어 기준으로 다시 하기 위한 묶음(2026-11-18 사용자 「모든 번역 영어기준으로」).

입력: work/translation/src/*.json(원문·영어·화자·줄 수·폭 한도), work/translation/ko.json(지금 번역), work/review2/locked.json
출력: work/review4/src/<묶음>.json — 원문 줄 + ko_now + locked. 원문이 들어 있어 커밋 금지.
G_ui 는 커서 둘로 나눔.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TR = os.path.join(ROOT, 'work', 'translation')
OUT = os.path.join(ROOT, 'work', 'review4', 'src')


def main():
    ko = json.load(open(os.path.join(TR, 'ko.json'), encoding='utf-8'))
    locked = json.load(open(os.path.join(ROOT, 'work', 'review2', 'locked.json'), encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for f in sorted(os.listdir(os.path.join(TR, 'src'))):
        if not f.endswith('.json'):
            continue
        rows = [r for r in json.load(open(os.path.join(TR, 'src', f), encoding='utf-8')) if r['key'] in ko]
        for r in rows:
            r['ko_now'] = ko[r['key']]
            r['locked'] = r['key'] in locked
        name = f[:-5]
        parts = [(name, rows)]
        if name == 'G_ui':
            h = len(rows) // 2
            parts = [('G1_ui', rows[:h]), ('G2_ui', rows[h:])]
        for n, rs in parts:
            json.dump(rs, open(os.path.join(OUT, n + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(n, len(rs), '영어 없음', sum(1 for r in rs if not (r.get('en') or '').strip()), '고정', sum(r['locked'] for r in rs))
            total += len(rs)
    print('합계', total, '/', len(ko))


if __name__ == '__main__':
    main()
