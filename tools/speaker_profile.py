"""화자별 말투 자료: 1인칭·2인칭·존댓말 비율·대화 상대(같은 장면에서 바로 앞뒤 다른 화자)·예문.

자막 순서: DT_Chapter_* 의 Subs_* 구역 안 L_### 번호 순.
출력: work/survey/speaker_profile.txt
"""
import collections
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRST = ['俺', 'オレ', 'おれ', '私', 'わたし', 'アタシ', 'あたし', 'ワシ', 'わし', '僕', 'ボク', '我々', 'われわれ', 'オレたち', '俺たち', '自分']
SECOND = ['おまえ', 'お前', 'オマエ', 'てめえ', 'テメエ', 'てめぇ', 'あんた', 'アンタ', '貴様', 'キサマ', 'キミ', '君', 'あなた', 'お前さん', 'オメエ']
POLITE = re.compile(r'(です|ます|ません|ください|でした|ましょう|下さい|ございます)')
PLAIN = re.compile(r'(だ|ぞ|ぜ|な|よ|ろ|か|ねえ|んだ|じゃ|わ|の)[!?！？ 　…]*$')


def main():
    r = json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
    subs = [x for x in r if x['group'] == 'story_sub' and x.get('speaker') is not None and re.match(r'^L_\d+$', x['name'])]
    scenes = collections.defaultdict(list)
    for x in subs:
        scenes[(x['file'], x['section'])].append(x)
    for k in scenes:
        scenes[k].sort(key=lambda x: int(x['name'][2:]))
    prof = collections.defaultdict(lambda: {'n': 0, 'pol': 0, 'first': collections.Counter(), 'second': collections.Counter(),
                                            'to': collections.Counter(), 'ex': []})
    pair_pol = collections.Counter()
    pair_n = collections.Counter()
    for k, lines in scenes.items():
        for i, x in enumerate(lines):
            s = x['speaker'] or '(없음)'
            p = prof[s]
            p['n'] += 1
            t = x['jp']
            pol = bool(POLITE.search(t))
            p['pol'] += pol
            for w in FIRST:
                if w in t:
                    p['first'][w] += 1
            for w in SECOND:
                if w in t:
                    p['second'][w] += 1
            nb = [lines[j]['speaker'] for j in (i - 1, i + 1) if 0 <= j < len(lines) and lines[j]['speaker'] != s]
            for o in set(nb):
                p['to'][o] += 1
                pair_n[(s, o)] += 1
                pair_pol[(s, o)] += pol
            if len(p['ex']) < 6 and len(t) > 6:
                p['ex'].append('%s/%s: %s' % (x['file'].replace('DT_Chapter_', 'Ch'), x['section'], t.replace('\n', ' / ')))
    out = []
    for s, p in sorted(prof.items(), key=lambda kv: -kv[1]['n']):
        out.append('■ %s  %d줄  존댓말 %d%%' % (s, p['n'], 100 * p['pol'] // max(p['n'], 1)))
        out.append('  1인칭 %s | 2인칭 %s' % (dict(p['first'].most_common(4)), dict(p['second'].most_common(4))))
        tos = []
        for o, c in p['to'].most_common(6):
            tos.append('%s(%d, 존댓말 %d%%)' % (o, c, 100 * pair_pol[(s, o)] // max(pair_n[(s, o)], 1)))
        out.append('  대화 상대 ' + ', '.join(tos))
        for e in p['ex']:
            out.append('    ' + e)
    open(os.path.join(ROOT, 'work', 'survey', 'speaker_profile.txt'), 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
