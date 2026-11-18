"""처음부터 다시 번역(2026-11-18 사용자 「다시 처음부터 다 번역해 너 혼자해라」) 작업 도구.
에이전트 없이 Claude 가 장면 순서대로 직접 번역한다.

  python -I -X utf8 tools/retr5.py plan            묶음 나누기 → work/retr5/plan.json
  python -I -X utf8 tools/retr5.py show <묶음>      묶음 내용(번호·화자·영어·일본어·지금 번역) 출력
  python -I -X utf8 tools/retr5.py put <묶음>       work/retr5/in/<묶음>.txt(「번호<TAB>번역」, 줄바꿈은 ⏎)를
                                                   work/retr5/out/<묶음>.json 으로 바꾸고 검사
  python -I -X utf8 tools/retr5.py merge           out 전부 + 안 바꾼 줄 → work/retr5/ko_new.json
"""
import collections
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'work', 'retr5')
NL = '⏎'


def load():
    src = json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    locked = json.load(open(os.path.join(ROOT, 'work', 'review2', 'locked.json'), encoding='utf-8'))
    rows = [x for x in src if x['key'] in ko]
    return rows, ko, locked


def plan():
    rows, ko, _ = load()
    # 자막 먼저(장 순서), 그다음 그 밖. 같은 파일·섹션은 끊지 않고 묶음 크기 약 120줄
    sub = [x for x in rows if x['kind'] == 'subtitle']
    other = [x for x in rows if x['kind'] != 'subtitle']
    chunks = []

    def cut(items, prefix, size=120):
        cur, n = [], 0
        sec = None
        for x in items:
            s = (x['file'], x['section'])
            if cur and len(cur) >= size and s != sec:
                chunks.append(('%s%02d' % (prefix, len(chunks) + 1), cur))
                cur = []
            cur.append(x['key'])
            sec = s
        if cur:
            chunks.append(('%s%02d' % (prefix, len(chunks) + 1), cur))

    cut(sub, 'S')
    by = collections.OrderedDict()
    for x in other:
        by.setdefault(x['file'], []).append(x)
    cut([x for f in by for x in by[f]], 'U')
    os.makedirs(os.path.join(W, 'in'), exist_ok=True)
    os.makedirs(os.path.join(W, 'out'), exist_ok=True)
    json.dump(collections.OrderedDict(chunks), open(os.path.join(W, 'plan.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for name, keys in chunks:
        fs = collections.Counter(k.split('|')[0] for k in keys)
        print(name, len(keys), dict(fs))
    print('묶음', len(chunks), '줄', sum(len(k) for _, k in chunks))


def show(name):
    rows, ko, locked = load()
    byk = {x['key']: x for x in rows}
    keys = json.load(open(os.path.join(W, 'plan.json'), encoding='utf-8'))[name]
    sec = None
    for i, k in enumerate(keys, 1):
        x = byk[k]
        s = (x['file'], x['section'])
        if s != sec:
            print('==== %s | %s' % s)
            sec = s
        lim = '줄%d' % x['lines'] + ('' if x['kind'] == 'subtitle' else ' em%.1f' % (x.get('limit_em') or 0))
        lk = ' 【고정:%s】' % locked[k] if k in locked else ''
        print('%d [%s] %s %s%s' % (i, x.get('speaker') or '-', x['name'], lim, lk))
        print('  E:', (x.get('en') or '').replace('\n', NL))
        print('  J:', (x.get('jp') or '').replace('\n', NL))
        print('  N:', ko[k].replace('\n', NL))


def put(name):
    keys = json.load(open(os.path.join(W, 'plan.json'), encoding='utf-8'))[name]
    rows, ko, _ = load()
    got = {}
    for ln in open(os.path.join(W, 'in', name + '.txt'), encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip():
            continue
        i, t = ln.split('\t', 1)
        i = int(i)
        assert 1 <= i <= len(keys), i
        assert i not in got, ('번호 겹침', i)
        got[i] = t.replace(NL, '\n')
    miss = [i for i in range(1, len(keys) + 1) if i not in got]
    if miss:
        raise SystemExit('빠진 번호 %s' % miss)
    out = {keys[i - 1]: got[i] for i in range(1, len(keys) + 1)}
    p = os.path.join(W, 'out', name + '.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    ch = sum(1 for k in out if out[k] != ko[k])
    print('줄', len(out), '바뀐 줄', ch)
    sp = os.path.join(W, 'src_' + name + '.json')
    byk = {x['key']: x for x in rows}
    json.dump([byk[k] for k in keys], open(sp, 'w', encoding='utf-8'), ensure_ascii=False)
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(ROOT, 'tools', 'check_translation.py'), p,
                        '--src', sp], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout[-3000:], r.stderr[-2000:])


def merge():
    rows, ko, _ = load()
    plan_ = json.load(open(os.path.join(W, 'plan.json'), encoding='utf-8'))
    new = dict(ko)
    done = 0
    for name in plan_:
        p = os.path.join(W, 'out', name + '.json')
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            new.update(d)
            done += 1
    json.dump(new, open(os.path.join(W, 'ko_new.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('끝난 묶음', done, '/', len(plan_), '바뀐 줄', sum(1 for k in ko if new[k] != ko[k]))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'plan':
        plan()
    elif cmd == 'show':
        show(sys.argv[2])
    elif cmd == 'put':
        put(sys.argv[2])
    elif cmd == 'merge':
        merge()
