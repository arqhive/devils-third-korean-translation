"""자막 대사 영어 기준 재번역 반영(2026-11-18).

work/review3/changes.json(담당 7명 결과 중 바뀐 줄) + 내가 고친 것(FIX) → 덩어리 번역(work/translation/out)에 넣음.
사용: python -I -X utf8 tools/apply_review3.py           → 조회만(개수·고친 줄 출력, changes_final.json)
      python -I -X utf8 tools/apply_review3.py --apply   → 넣기
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
W = os.path.join(ROOT, 'work', 'review3')

# 검수에서 내가 고친 것: 키 → 새 글(None = 바꾸지 않고 지금 번역 유지)
FIX = {
    # 사용자 결정 ④(11/17) 「아이반 → 밥 일행 『당신들』 유지」와 어긋남 → 「당신들」로, 내용은 en(임무)
    'DT_Chapter_03|Subs_C040|L_001': '대위, 나한텐 내 방식이 있어.\n하지만 당신들한테도 당신들 임무가 있다는 건 알아.\n사냥 시간이다.',
    # 「네놈, … 냈겠다!」 어색 → en "You fucked him up!"
    'DT_Chapter_01|Subs_R010|L_002': '네놈이 저 녀석을 작살 냈어!',
    # en "Too hot, damn!" 뜻이 장면에서 불분명 → 지금 번역 유지
    'DT_Chapter_08_Mg1|Subs_Set05|L_002': None,
}


def main():
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    ch = json.load(open(os.path.join(W, 'changes.json'), encoding='utf-8'))
    final = {}
    for k, (b, a) in ch.items():
        assert ko[k] == b, k
        if k in FIX:
            if FIX[k] is None:
                continue
            a = FIX[k]
        if a != b:
            final[k] = (b, a)
    assert all(k in ch for k, v in FIX.items() if v is not None)
    json.dump(final, open(os.path.join(W, 'changes_final.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('담당 결과 바뀐 줄', len(ch), '내가 고침', sum(1 for v in FIX.values() if v), '되돌림',
          sum(1 for v in FIX.values() if v is None), '최종', len(final))
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
            if key in final:
                assert d[key] == final[key][0], key
                d[key] = final[key][1]
                hit.add(key)
                chg = True
        if chg:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert hit == set(final)
    print('반영', len(hit))


if __name__ == '__main__':
    main()
