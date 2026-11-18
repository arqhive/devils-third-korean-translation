"""글상자 ↔ 번역 키 연결(기본 글 일치) 조사.

글상자 기본 글(태그 뺀 글)이 INT·JPN·FRA 의 값과 정확히 같으면 그 키에 연결한다.
출력: work/survey/winmap.json, work/survey/winmap_report.txt
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'work', 'survey')


def loc_values(lang):
    f = json.load(open(os.path.join(ROOT, 'work', 'extract', 'coalesced', lang + '.json'), encoding='utf-8'))
    out = collections.defaultdict(list)
    for n, s in f:
        if 'Localization' not in n['s']:
            continue
        fn = n['s'].split('\\')[-1].rsplit('.', 1)[0]
        for sn, ks in s:
            for k, v in ks:
                out[v['s'].strip()].append('%s|%s|%s' % (fn, sn['s'], k['s']))
    return out


def main():
    edits = json.load(open(os.path.join(S, 'edits_all.json'), encoding='utf-8'))
    vals = {L: loc_values(L) for L in ('INT', 'JPN', 'FRA')}
    res = []
    hit = collections.Counter()
    for m, v in edits.items():
        for e in v.get('edits', []):
            t = re.sub('<[^>]+>', '', e.get('text', '')).replace('&amp;', '&').strip()
            keys = []
            for L in ('JPN', 'INT', 'FRA'):
                if t and t in vals[L]:
                    keys = vals[L][t]
                    hit[L] += 1
                    break
            res.append({'movie': m, 'id': e['id'], 'inst': e['inst'], 'var': e['var'], 'font': e['font'],
                        'size': e.get('size'), 'w': e['w'], 'h': e['h'], 'multiline': e['multiline'],
                        'wordwrap': e['wordwrap'], 'autosize': e['autosize'], 'align': e.get('align'),
                        'lmargin': e.get('lmargin'), 'rmargin': e.get('rmargin'), 'leading': e.get('leading'),
                        'text': t, 'keys': keys})
    json.dump(res, open(os.path.join(S, 'winmap.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    nk = sum(1 for r in res if r['keys'])
    keyset = {k for r in res for k in r['keys']}
    with open(os.path.join(S, 'winmap_report.txt'), 'w', encoding='utf-8') as f:
        f.write('boxes %d, matched %d (%s), distinct keys %d\n' % (len(res), nk, dict(hit), len(keyset)))
        for r in res:
            if r['keys']:
                f.write('%s|%s|%s|%s|w=%s|%s\n' % (r['movie'], r['inst'], r['font'], r['size'], r['w'], r['keys'][:3]))


if __name__ == '__main__':
    main()
