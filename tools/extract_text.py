"""번역용 원문 JSON 만들기(Coalesced_JPN 의 Localization 파일들).

대상: 일본어(가나·한자)가 든 값. 같은 키의 영어(INT)·프랑스어(FRA)를 참고로 붙인다.
자막(DT_Chapter_*/Subs_*/L_###)은 화자(L_###_chr)와 이전·다음 줄 번호를 붙인다.
범위(scope): solo 번역 / mp 멀티라 뺌 / data 자료(번역 금지) — tools/scope_rules.py
분류(group): story_sub(자막), story(장 임무·제목 등), ui, mp(멀티·온라인), manual, collect, weapon, tips, engine
출력:
  work/extract/text_jpn.json    [{key, file, section, name, group, kind, jp, en, fr, speaker, lines, limit}]
  work/extract/speakers.json    화자별 줄 수
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure  # noqa: E402
import scope_rules  # noqa: E402

ROOT = os.path.dirname(HERE)
JP = re.compile('[぀-ヿ一-鿿]')
MP = re.compile(r'(?i)multiplay|clan|mapedit|ranking|charamake|shop|loadout|playernotice|dsr_map|e_shop|unlockgore')


def group_of(fn, sec, key):
    f = fn.lower()
    if f.startswith('dt_chapter_') and sec.startswith('Subs_'):
        return 'story_sub'
    if f.startswith('dt_chapter_'):
        return 'story'
    if f.startswith('dt_voice_chapter'):
        return 'voice_meta'
    if f in ('core', 'engine', 'ipdrv', 'launch', 'startup', 'subtitles', 'editormaptemplates', 'onlinesubsystemgamespy'):
        return 'engine'
    if f == 'dt_manual':
        return 'manual'
    if f == 'dt_collectitems':
        return 'collect'
    if f.startswith('dt_weapons'):
        return 'weapon'
    if f == 'dt_tips':
        return 'tips'
    if MP.search(f):
        return 'mp'
    return 'ui'


def main():
    vals = {L: measure.load_coal(L) for L in ('JPN', 'INT', 'FRA')}
    lim = json.load(open(os.path.join(ROOT, 'work', 'survey', 'limits.json'), encoding='utf-8'))['keys']
    rows = []
    spk = collections.Counter()
    for key, jp in vals['JPN'].items():
        if not JP.search(jp):
            continue
        fn, sec, name = key.split('|')
        g = group_of(fn, sec, name)
        row = {'key': key, 'file': fn, 'section': sec, 'name': name, 'group': g,
               'scope': scope_rules.scope_of(fn, sec),
               'jp': jp, 'en': vals['INT'].get(key), 'fr': vals['FRA'].get(key)}
        if g == 'story_sub' and re.match(r'^L_\d+$', name):
            s = vals['JPN'].get(key + '_chr', '')
            row['speaker'] = s
            spk[s] += 1
        L = lim.get(key)
        if L:
            row['kind'] = L['kind']
            row['lines'] = L['lines']
            if L['kind'] == 'ui':
                row['limit_em'] = L['w_em']
        rows.append(row)
    out = os.path.join(ROOT, 'work', 'extract')
    json.dump(rows, open(os.path.join(out, 'text_jpn.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(dict(spk.most_common()), open(os.path.join(out, 'speakers.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    g = collections.Counter(r['group'] for r in rows)
    gc = collections.Counter()
    for r in rows:
        gc[r['group']] += len(r['jp'])
    with open(os.path.join(ROOT, 'work', 'survey', 'text_groups.txt'), 'w', encoding='utf-8') as f:
        for k, v in g.most_common():
            f.write('%s\t%d\t%d\n' % (k, v, gc[k]))
        f.write('speakers %d\n' % len(spk))
        for k, v in spk.most_common():
            f.write('  %s\t%d\n' % (k, v))


if __name__ == '__main__':
    main()
