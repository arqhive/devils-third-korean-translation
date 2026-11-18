"""새 번역 규칙 재검수 반영 1단계(2026-11-17 사용자 결정).

work/review2/proposals.json 의 제안을 덩어리 번역(work/translation/out)에 넣는다.
- 결정 묶음 ①②⑥⑦⑬: 검수 안대로
- ⑮ 시스템 あなた: 검수 안에서 「우리 클랜」 → 「소속 클랜」
- ③ AC-130 조종사: 「어긋난 건 당신이야!」 → 「어긋난 건 너야!」
- ④⑤⑪: 그대로(반영 안 함)
- ⑧⑨⑩⑫⑭: 2단계(해당 줄을 모두 찾아 대조표로 다시 승인)
- 그 밖(결정 묶음 아님): 제안대로
수정 전 글이 덩어리 파일과 다르면 멈춘다. 결과 기록 work/review2/applied1.txt
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
W = os.path.join(ROOT, 'work', 'review2')
USE = {'①', '②', '⑥', '⑦', '⑬', '⑮', None}
LATER = {'⑧', '⑨', '⑩', '⑫', '⑭'}


def main():
    props = json.load(open(os.path.join(W, 'proposals.json'), encoding='utf-8'))
    want = {}
    for x in props:
        d = x['decide']
        if d in LATER or d not in USE:
            continue
        text = x['proposal']
        if d == '⑮':
            text = text.replace('우리 클랜', '소속 클랜')
        if text != x['before']:
            want[x['key']] = (x['before'], text)
    k = 'DT_Chapter_02|Subs_R190|L_012'
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    assert '어긋난 건 당신이야!' in ko[k]
    want[k] = (ko[k], ko[k].replace('어긋난 건 당신이야!', '어긋난 건 너야!'))
    log, hit = [], set()
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        ch = False
        for key in d:
            if key in want:
                before, after = want[key]
                assert d[key] == before, ('수정 전 글이 다름', key)
                d[key] = after
                hit.add(key)
                ch = True
                log.append('%s\n  전 %s\n  후 %s' % (key, before.replace('\n', '/'), after.replace('\n', '/')))
        if ch:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert hit == set(want), set(want) - hit
    open(os.path.join(W, 'applied1.txt'), 'w', encoding='utf-8').write('\n'.join(log))
    print('반영', len(hit))


if __name__ == '__main__':
    main()
