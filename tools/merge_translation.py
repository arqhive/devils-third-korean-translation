"""덩어리별 번역(work/translation/out/*.json)을 하나로 합치고 전체 검사, 질문거리(notes) 모으기.
출력: work/translation/ko.json, work/translation/notes_all.json
사용: python -I -X utf8 tools/merge_translation.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_translation  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'work', 'translation', 'out')


def main():
    ko = {}
    notes = {}
    dup = []
    for f in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, f)
        if f.endswith('.notes.json'):
            for k, v in json.load(open(p, encoding='utf-8')).items():
                notes['%s|%s' % (f[:-11], k)] = v
            continue
        if not f.endswith('.json'):
            continue
        for k, v in json.load(open(p, encoding='utf-8')).items():
            if k in ko:
                dup.append(k)
            ko[k] = v
    json.dump(ko, open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump(notes, open(os.path.join(ROOT, 'work', 'translation', 'notes_all.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    src = json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
    issues = check_translation.check(ko, src, check_translation.Widths())
    for k, m in issues:
        print('%s\t%s' % (k, m))
    print('합친 줄 %d, 중복 %d, 질문거리 %d, 문제 %d' % (len(ko), len(dup), len(notes), len(issues)))


if __name__ == '__main__':
    main()
