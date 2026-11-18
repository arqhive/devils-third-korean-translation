"""용어 후보 뽑기(번역 범위 solo 만): 가타카나 낱말(・ 로 이어진 이름 포함)·한자어 빈도, 예문(일·영).
출력: work/survey/term_candidates.txt
"""
import collections
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KATA = re.compile(r'[ァ-ヴー][ァ-ヴー・ ]*[ァ-ヴー]|[A-Z][A-Za-z0-9\-]+')
KANJI = re.compile(r'[一-鿿]{2,6}')
STOP_K = {'ヤツ', 'ヤツら', 'コイツ', 'アイツ', 'クソ', 'ムショ', 'バカ', 'イヤ', 'オイ', 'ハズ', 'モノ', 'ダメ', 'ブッ', 'ヤバイ'}


def main():
    r = [x for x in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
         if x['scope'] == 'solo']
    kc = collections.Counter()
    hc = collections.Counter()
    ex = {}
    for x in r:
        t = x['jp']
        for m in KATA.findall(t):
            m = re.sub(r'\s*・\s*', '・', m.strip())
            if len(m) < 2 or m in STOP_K:
                continue
            kc[m] += 1
            ex.setdefault(m, (x['key'], t, x.get('en')))
        for m in KANJI.findall(t):
            hc[m] += 1
            ex.setdefault(m, (x['key'], t, x.get('en')))
    out = ['=== 가타카나·영문 (2회 이상, 이름은 1회도)']
    for w, n in kc.most_common():
        if n < 2 and '・' not in w:
            continue
        k, t, en = ex[w]
        out.append('%s\t%d\t%s\t%s\t%s' % (w, n, k, t.replace('\n', '/')[:60], (en or '').replace('\n', '/')[:70]))
    out.append('=== 한자어 (4회 이상)')
    for w, n in hc.most_common():
        if n < 4:
            break
        k, t, en = ex[w]
        out.append('%s\t%d\t%s\t%s\t%s' % (w, n, k, t.replace('\n', '/')[:60], (en or '').replace('\n', '/')[:70]))
    open(os.path.join(ROOT, 'work', 'survey', 'term_candidates.txt'), 'w', encoding='utf-8').write('\n'.join(out))
    print(len(out))


if __name__ == '__main__':
    main()
