"""영어 기준 자막 재번역 대조표(2026-11-18).

입력: work/review3/src/*.json(jp·en·ko_now·speaker·locked), work/review3/out/<묶음>.json·.why.json·.notes.json
출력: work/review3/영어기준_대조표.html, work/review3/changes.json({key: [전, 후]})
검사: 바뀐 줄의 높임(존댓말 ↔ 반말) 변화, 줄바꿈 수 증가, 고정 줄 변경 → 표에 표시
사용: python -I -X utf8 tools/review3_table.py [review4]   (기본 review3, 11/18 모든 번역 영어 기준은 review4)
"""
import collections
import difflib
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'work', sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith('review') else 'review3')
POLITE = re.compile(r'(습니다|습니까|ㅂ니다|니다|세요|에요|예요|해요|어요|아요|지요|죠|요)[.!?…\s~]*$')


def polite(s):
    """줄마다 존댓말 끝맺음이면 1, 아니면 0(태그·이름표 뺌)."""
    s = re.sub(r'~/?COL[^~]*~', '', s)
    out = []
    for ln in s.split('\n'):
        ln = ln.strip()
        if not ln:
            continue
        out.append(1 if POLITE.search(ln) else 0)
    return out


def diff(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    oa, ob = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        sa, sb = html.escape(a[i1:i2]), html.escape(b[j1:j2])
        if op == 'equal':
            oa.append(sa)
            ob.append(sb)
        else:
            if sa:
                oa.append('<del>%s</del>' % sa)
            if sb:
                ob.append('<ins>%s</ins>' % sb)
    return ''.join(oa).replace('\n', '<br>'), ''.join(ob).replace('\n', '<br>')


def main():
    srcs = sorted(f[:-5] for f in os.listdir(os.path.join(W, 'src')) if f.endswith('.json'))
    rows, changes, stat = [], {}, collections.Counter()
    for name in srcs:
        items = json.load(open(os.path.join(W, 'src', name + '.json'), encoding='utf-8'))
        p = os.path.join(W, 'out', name + '.json')
        if not os.path.exists(p):
            print('결과 없음', name)
            continue
        out = json.load(open(p, encoding='utf-8'))
        why = json.load(open(os.path.join(W, 'out', name + '.why.json'), encoding='utf-8')) \
            if os.path.exists(os.path.join(W, 'out', name + '.why.json')) else {}
        notes = json.load(open(os.path.join(W, 'out', name + '.notes.json'), encoding='utf-8')) \
            if os.path.exists(os.path.join(W, 'out', name + '.notes.json')) else {}
        keys = {i['key'] for i in items}
        assert set(out) == keys, (name, len(set(out) ^ keys))
        for it in items:
            k = it['key']
            stat['입력'] += 1
            b, a = it['ko_now'], out[k]
            if a == b:
                continue
            flags = []
            if polite(b) != polite(a) and len(polite(b)) == len(polite(a)):
                flags.append('높임 바뀜')
            if a.count('\n') > b.count('\n'):
                flags.append('줄 늘어남')
            if it['locked']:
                flags.append('고정 줄')
            if k in notes:
                flags.append('질문')
            for f in flags:
                stat[f] += 1
            stat['바뀜'] += 1
            changes[k] = [b, a]
            rows.append((name, it, b, a, why.get(k, ''), notes.get(k, ''), flags))
    json.dump(changes, open(os.path.join(W, 'changes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    out = ['<!doctype html><html lang="ko"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1"><title>영어 기준 대조표</title>'
           '<style>body{font:14px/1.55 "Malgun Gothic",sans-serif;margin:16px;background:#fff;color:#1d1d1f}'
           '@media (prefers-color-scheme: dark){body{background:#1c1c1e;color:#f2f2f7}td,th{border-color:#555}}'
           'table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;vertical-align:top}'
           'del{background:#ffdede;color:#000}ins{background:#d9f5df;text-decoration:none;color:#000}'
           '.k{font-size:11px;color:#888}.f{color:#c00;font-weight:bold}.n{color:#a60}</style></head><body>'
           '<h1>자막 대사 영어 기준 재번역 대조표</h1>'
           '<p>' + html.escape(json.dumps(dict(stat), ensure_ascii=False)) + '</p>'
           '<table><tr><th>#</th><th>화자·키</th><th>일본어</th><th>영어</th><th>수정 전</th><th>수정 후</th>'
           '<th>바꾼 이유·질문</th></tr>']
    for i, (name, it, b, a, w, n, flags) in enumerate(rows, 1):
        db, da = diff(b, a)
        out.append('<tr><td>%d</td><td>%s<div class="k">%s</div><div class="f">%s</div></td><td>%s</td><td>%s</td>'
                   '<td>%s</td><td>%s</td><td>%s%s</td></tr>' % (
                       i, html.escape(it.get('speaker') or ''), html.escape(it['key']), ' · '.join(flags),
                       html.escape(it['jp']).replace('\n', '<br>'), html.escape(it.get('en') or '').replace('\n', '<br>'),
                       db, da, html.escape(w), ('<div class="n">질문: %s</div>' % html.escape(n)) if n else ''))
    out.append('</table></body></html>')
    name = '영어기준_대조표.html' if W.endswith('review3') else '전체_영어기준_대조표.html'
    open(os.path.join(W, name), 'w', encoding='utf-8').write('\n'.join(out))
    print(dict(stat))


if __name__ == '__main__':
    main()
