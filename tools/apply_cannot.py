"""안내문 「~할 수 없었습니다」 → 「~할 수 없습니다」(2026-11-18 사용자 지시, 대조표 10줄 승인).
수집 문서 IF_03·IF_06(지난 역사 서술)은 뺌.

사용: python -I -X utf8 tools/apply_cannot.py          → 조회만
      python -I -X utf8 tools/apply_cannot.py --apply  → 덩어리 번역(work/translation/out)에 넣음
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))

KEYS = [
    'DT_UI_MessageBox|ErrorMessages|E_158',
    'DT_UI_MessageBox|Messages|CapacityOver',
    'DT_UI_MessageBox|Messages|ScoreUploadFailure',
    'DT_UI_MessageBox|Messages_Error|ErrorCreateMatch',
    'DT_UI_MessageBox|Messages_Error|ErrorJoinMatch',
    'DT_UI_MessageBox|Messages_Error|ErrorScoreUpload',
    'DT_UI_MessageBox|Messages_Error|ErrorStartMatch',
    'DT_UI_MessageBox|Messages_Network|CannotConnect',
    'DT_UI_MessageBox|Messages_Notice|NoticeFailedToLoadMapEdit',
    'DT_UI_MessageBox|Messages_Warning|WarningConditionUnsatisfiedStartWar',
]
SKIP = {'DT_CollectItems|Descriptions|IF_03', 'DT_CollectItems|Descriptions|IF_06'}


def main():
    found = sorted(k for k, v in ko.items() if '수 없었습니다' in v)
    assert found == sorted(KEYS), found
    assert all('없었습니다' not in ko[k] for k in SKIP)
    want = {}
    for k in KEYS:
        assert ko[k].count('수 없었습니다') == 1, k
        want[k] = (ko[k], ko[k].replace('수 없었습니다', '수 없습니다'))
        print(k, '|', want[k][1].replace('\n', '/'))
    if '--apply' not in sys.argv:
        return
    hit = set()
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        ch = False
        for key in d:
            if key in want:
                assert d[key] == want[key][0], key
                d[key] = want[key][1]
                hit.add(key)
                ch = True
        if ch:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert hit == set(want)
    print('반영', len(hit))


if __name__ == '__main__':
    main()
