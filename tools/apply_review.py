"""7단계 검수 반영(2026-11-06 사용자 승인). work/review/proposals.json 의 제안을 덩어리 파일(work/translation/out)에 넣는다.
사용자 결정: 有効 5줄은 「효과적」 그대로(반영 안 함), 나머지(おいおい 4줄·注意 2줄·내 안·높음·보통·낮음)는 제안대로.
수정 전 글이 덩어리 파일과 다르면 멈춘다(그 사이 바뀐 줄을 덮어쓰지 않게).
결과 기록: work/review/applied.txt
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
SKIP_GROUPS = {'decide:有効'}


def main():
    props = json.load(open(os.path.join(ROOT, 'work', 'review', 'proposals.json'), encoding='utf-8'))
    by_key = {p['key']: p for p in props if p['group'] not in SKIP_GROUPS and p['proposal'] != p['before']}
    log, hit = [], set()
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        ch = False
        for k in d:
            if k in by_key:
                x = by_key[k]
                assert d[k] == x['before'], ('수정 전 글이 다름', k)
                d[k] = x['proposal']
                hit.add(k)
                ch = True
                log.append('%d %s\n  전 %s\n  후 %s' % (x['no'], k, x['before'].replace('\n', '/'), x['proposal'].replace('\n', '/')))
        if ch:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    missing = set(by_key) - hit
    assert not missing, missing
    open(os.path.join(ROOT, 'work', 'review', 'applied.txt'), 'w', encoding='utf-8').write('\n'.join(log))
    print('반영', len(hit), '/ 그대로 둔 결정 그룹', sorted(SKIP_GROUPS))


if __name__ == '__main__':
    main()
