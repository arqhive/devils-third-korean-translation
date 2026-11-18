"""덩어리끼리 갈린 용어 통일(2026-11-06 사용자 결정) — 원문에 그 용어가 든 줄만 바꾸고 조사도 맞춘다.
결정: ドレン=돌렌 / 修復=수복 / エリア=시스템(메뉴·메시지·UI) 에어리어, 대사(자막·임무) 구역 / 金の卵=황금알 /
      苦界行=고계행 / 日米露=미일러(日米=미일) / 화면 위 시간 표시 = 「현지 시간 M월 D일 HH:MM」
출력: 덩어리 파일을 고쳐 씀, 바뀐 줄 표 work/survey/unify_diff.txt
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')

# 받침 있는 말 ↔ 없는 말로 바뀔 때 조사 바꾸기
JOSA_TO_BATCHIM = [('를', '을'), ('가', '이'), ('는', '은'), ('로', '으로'), ('와', '과'), ('라', '이라'), ('야', '이야')]


def swap(text, old, new, new_has_batchim, old_has_batchim):
    def rep(m):
        j = m.group(1) or ''
        if new_has_batchim and not old_has_batchim:
            for a, b in JOSA_TO_BATCHIM:
                if j == a:
                    j = b
                    break
        elif old_has_batchim and not new_has_batchim:
            for a, b in JOSA_TO_BATCHIM:
                if j == b:
                    j = a
                    break
        return new + j
    return re.sub(re.escape(old) + r'(으로|이라|이야|[을를이가은는로와과라야])?', rep, text)


def telop(jp):
    s = re.sub(r'\s+', '', jp)
    m = re.match(r'現地時間(\d+)月(\d+)日(\d+)時(\d+)分', s)
    if not m:
        return None
    mo, d, h, mi = (int(x) for x in m.groups())
    return '현지 시간 %d월 %d일 %d:%02d' % (mo, d, h, mi)


def main():
    src = {r['key']: r for r in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))}
    diff = []
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        story = f[0] in 'ABCD'
        for k, v in list(d.items()):
            jp = src[k]['jp']
            n = v
            if 'ドレン' in jp:
                n = n.replace('드렌', '돌렌').replace('도렌', '돌렌')
            if '修復' in jp:
                n = swap(n, '수리', '수복', True, False)
            if 'エリア' in jp:
                if story:
                    n = n.replace('지역', '구역')
                    n = swap(n, '에어리어', '구역', True, False)
                else:
                    n = swap(n, '지역', '에어리어', False, True)
                    n = swap(n, '구역', '에어리어', False, True)
            if '金の卵' in jp:
                n = n.replace('금의 알', '황금알')
            if '苦界' in jp:
                n = n.replace('고해행', '고계행')
            if '日米露' in jp:
                n = n.replace('일미러', '미일러')
            elif '日米' in jp:
                n = n.replace('일미 ', '미일 ')
            if src[k]['section'] == 'Telops' and '現地時間' in jp:
                t = telop(jp)
                if t:
                    n = t
            if n != v:
                d[k] = n
                diff.append('%s\t%s\n  원문 %s\n  전   %s\n  후   %s' % (f[:-5], k, jp.replace('\n', '/'), v.replace('\n', '/'),
                                                                   n.replace('\n', '/')))
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(ROOT, 'work', 'survey', 'unify_diff.txt'), 'w', encoding='utf-8').write('\n'.join(diff))
    print('바뀐 줄', len(diff))


if __name__ == '__main__':
    main()
