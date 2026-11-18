"""자막 살리기(2026-11-18 사용자 「다시해봐, 욕 넣어 과격한 분위기는 잘했음」 → 0~1장 견본 승인 「1번으로 하고 나머지 장도」).
지금 번역(ko.json)을 기준으로 문제 있는 줄만 고친다(굳은 「~다.」 연속, 상대가 빠진 말, 뜻 어긋남, 욕 수위).
묶음 나누기는 retr5 의 plan.json(S01~S13) 을 그대로 쓴다.

  python -I -X utf8 tools/retr6.py show <묶음>    지금 번역 보기
  python -I -X utf8 tools/retr6.py put <묶음>     work/retr6/in/<묶음>.txt(「번호<TAB>새 번역」, 바꿀 줄만, 줄바꿈 ⏎) → out
  python -I -X utf8 tools/retr6.py check          모든 out 을 ko.json 에 얹은 사본으로 전체 검사
  python -I -X utf8 tools/retr6.py table          대조표 work/retr6/자막살리기_대조표.html
  python -I -X utf8 tools/retr6.py apply          out 을 work/translation/out/*.json 에 반영(사용자 승인 뒤)
"""
import html
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'work', 'retr6')
PLAN = os.path.join(ROOT, 'work', 'retr5', 'plan.json')
NL = '⏎'


def load():
    src = {x['key']: x for x in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))}
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    locked = json.load(open(os.path.join(ROOT, 'work', 'review2', 'locked.json'), encoding='utf-8'))
    plan = json.load(open(PLAN, encoding='utf-8'))
    return src, ko, locked, plan


def show(name):
    src, ko, locked, plan = load()
    sec = None
    for i, k in enumerate(plan[name], 1):
        x = src[k]
        s = (x['file'], x['section'])
        if s != sec:
            print('==== %s | %s' % s)
            sec = s
        lk = ' 【고정】' if k in locked else ''
        print('%d [%s] %s%s | E: %s | J: %s' % (i, x.get('speaker') or '-', x['name'], lk,
                                              (x.get('en') or '').replace('\n', NL), (x.get('jp') or '').replace('\n', NL)))
        print('   N: ' + ko[k].replace('\n', NL))


def outs():
    d = {}
    if os.path.isdir(os.path.join(W, 'out')):
        for f in sorted(os.listdir(os.path.join(W, 'out'))):
            if f.endswith('.json'):
                d.update(json.load(open(os.path.join(W, 'out', f), encoding='utf-8')))
    return d


def put(name):
    src, ko, locked, plan = load()
    keys = plan[name]
    os.makedirs(os.path.join(W, 'out'), exist_ok=True)
    got = {}
    p = os.path.join(W, 'in', name + '.txt')
    for ln in open(p, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip():
            continue
        i, t = ln.split('\t', 1)
        i = int(i)
        k = keys[i - 1]
        assert k not in got, ('겹침', i)
        t = t.replace(NL, '\n')
        if k in locked:
            raise SystemExit('고정 줄을 바꾸려 함: %d %s' % (i, k))
        if t == ko[k]:
            raise SystemExit('바뀐 게 없음: %d' % i)
        got[k] = t
    json.dump(got, open(os.path.join(W, 'out', name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s: %d줄 중 바꾼 줄 %d' % (name, len(keys), len(got)))
    check()


def check():
    src, ko, _, _ = load()
    new = dict(ko)
    new.update(outs())
    tmp = os.path.join(W, 'ko_check.json')
    json.dump(new, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(ROOT, 'tools', 'check_translation.py'), tmp],
                       capture_output=True, text=True, encoding='utf-8')
    print(r.stdout[-3000:], r.stderr[-2000:])


def table():
    src, ko, _, plan = load()
    d = outs()
    order = [k for n in plan for k in plan[n] if k in d]
    rows = []
    for k in order:
        x = src[k]
        e = lambda s: html.escape(s or '').replace('\n', '<br>')
        rows.append('<tr><td>%s<br><small>%s</small></td><td>%s</td><td>%s</td><td>%s</td><td class=n>%s</td></tr>' % (
            e(x.get('speaker') or '-'), e(k.split('|', 1)[1]), e(x.get('en')), e(x.get('jp')), e(ko[k]), e(d[k])))
    page = ('<!doctype html><meta charset=utf-8><title>자막 살리기 대조표</title><style>'
            'body{font-family:sans-serif;margin:16px;background:#fff;color:#111}table{border-collapse:collapse;width:100%}'
            'td,th{border:1px solid #ccc;padding:4px 6px;vertical-align:top;font-size:14px}th{background:#eee;position:sticky;top:0}'
            '.n{background:#eef8ee}small{color:#666}</style><h1>자막 살리기 대조표 (' + str(len(order)) + '줄)</h1>'
            '<table><tr><th>화자</th><th>영어</th><th>일본어</th><th>지금</th><th>수정</th></tr>' + ''.join(rows) + '</table>')
    p = os.path.join(W, '자막살리기_대조표.html')
    open(p, 'w', encoding='utf-8').write(page)
    print(p, len(order))


def apply():
    d = outs()
    od = os.path.join(ROOT, 'work', 'translation', 'out')
    hit = set()
    for f in sorted(os.listdir(od)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(od, f)
        j = json.load(open(p, encoding='utf-8'))
        ks = [k for k in j if k in d]
        for k in ks:
            j[k] = d[k]
            hit.add(k)
        if ks:
            json.dump(j, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert hit == set(d), set(d) - hit
    print('반영', len(hit))


if __name__ == '__main__':
    c = sys.argv[1]
    {'show': lambda: show(sys.argv[2]), 'put': lambda: put(sys.argv[2]), 'check': check, 'table': table,
     'apply': apply}[c]()
