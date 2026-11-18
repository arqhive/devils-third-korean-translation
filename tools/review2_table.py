"""새 번역 규칙(2026-11-16) 재검수 대조표 → work/review2/재검수_대조표.html, work/review2/proposals.json

입력: work/review2/ai_*.json(검수 담당 9명), notes_*.json(물을 것), locked.json
내가 바꾼 안(MINE)과 결정이 필요한 묶음(DECIDE)을 따로 보여 준다.
"""
import difflib
import glob
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'work', 'review2')
src = {r['key']: r for r in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))}
ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))

items = []
for p in sorted(glob.glob(glob.escape(W) + '/ai_*.json')):
    ch = os.path.basename(p)[3:-5]
    for x in json.load(open(p, encoding='utf-8')):
        x['chunk'] = ch
        x['proposal'] = x['after']
        x['note'] = ''
        items.append(x)
by = {x['key']: x for x in items}

# 내 판단으로 바꾼 안
K = 'DT_CollectItems|Descriptions|LQ_09'
by[K]['proposal'] = by[K]['before'].replace('일본주', '사케')
by[K]['note'] = '「환상의 → 전설의」는 뺌(5단계 사용자 결정 「전설의가 아니고 환상의」). 「일본주 → 사케」만 남김(결정 ⑨에 따름)'
K = 'DT_Chapter_09|Subs_C090|L_004'
by[K]['proposal'] = by[K]['before'].replace('너는 죽은 모체에서 떼어 내졌다.', '죽은 모체에서 너를 떼어 냈다.')
by[K]['note'] = '검수 안 「너는 …떼어 냈다」는 「너」가 떼어 낸 것처럼 읽혀 뜻이 바뀜 → 앞줄 「내가」를 주어로 이어 「죽은 모체에서 너를 떼어 냈다」'
MINE = {'DT_CollectItems|Descriptions|LQ_09', 'DT_Chapter_09|Subs_C090|L_004'}

# 결정이 필요한 묶음: (번호, 제목, 설명, 관련 키 목록)
DECIDE = [
    ('①', '아이반 → 캐러웨이(장관)를 부르는 アンタ', 'C010 L_010 등. 검수 안은 「댁」. 다른 후보: 「영감」·「장관」·빼기',
     ['DT_Chapter_01|Subs_C010|L_010']),
    ('②', '스텔라 → 아이반 あなた', '검수 안은 「네」 또는 빼기. 다른 후보: 「아이반」 이름',
     [k for k in by if '8-2' in str(by[k]['rule']) and src[k].get('speaker') in ('Stella', None) and k.startswith('DT_Chapter_02|')]),
    ('③', 'AC-130 조종사의 あんた(R190 L_012)', '지금 「당신」(시비조). 바로 다음 고정 줄은 「네 눈은」이라 당신/너가 섞임',
     ['DT_Chapter_02|Subs_R190|L_012']),
    ('④', '아이반 → 처음 만난 밥 일행 あんたら(C040 L_001)', '지금 「당신들」. 「너희」로 바꿀지',
     ['DT_Chapter_03|Subs_C040|L_001']),
    ('⑤', '아이반 → 포로 마에다 교수 アンタ(6장 C070 L_004)', '지금 「당신」(총 든 심문). 「댁」·「영감」 후보',
     ['DT_Chapter_06|Subs_C070|L_004']),
    ('⑥', '제인 → 아이반 アンタ 5줄', '검수 안은 「너」. 옛 연인이라 「당신」을 남길 수도',
     [k for k in by if '8-2' in str(by[k]['rule']) and src[k].get('speaker') == 'Jane']),
    ('⑦', '골드 팀 대장 → 아이반 あんた(첫 무전)', '검수 안은 「그쪽」·빼기. 다른 후보: 「자네」·이름',
     [k for k in by if '8-2' in str(by[k]['rule']) and src[k].get('speaker') == 'GoldTeamCaptain']),
    ('⑧', '光学迷彩·ステルス迷彩装甲', '지금 「광학 미채·스텔스 미채 장갑」. 본문 「스텔스 미채 장갑」만 「스텔스 위장 장갑」으로?',
     ['DT_CollectItems|Descriptions|EB_07']),
    ('⑨', '日本酒 「일본주」 → 「사케」·「일본 술」?', 'LQ_06(제목·본문), LQ_09 본문', ['DT_CollectItems|Descriptions|LQ_06',
                                                                                  'DT_CollectItems|Descriptions|LQ_09']),
    ('⑩', '献金 「헌금」 → 「기부」?', '클랜에 돌렌을 내는 것. 메시지·메뉴 여러 곳 → 용어로 정함', ['DT_UI_MessageBox|Messages|DonationTax']),
    ('⑪', '스코어 업로드 확인 높임', '게임 밖 조작으로 보고 「~하시겠습니까?」로 할지(랭킹 Upload 고정 줄의 「괜찮습니까?」 포함)',
     ['DT_UI_MessageBox|Messages|ScoreUploadFailure', 'DT_UI_Labels_Ranking|ScoreLabels|Upload']),
    ('⑫', '무기 설명 「미국의 맥풀사」 꼴(약 25줄)', '「의」를 빼서 「미국 맥풀사」로 할지(2-2). 이번 안에는 안 들어 있음',
     ['DT_Weapons|NormalWeapons_Descriptions|Id_17']),
    ('⑬', '인물 팁 「퍼스널 데이터」 9줄 → 「신상 정보」', '검수 안. 외래어 표제를 남길지',
     [k for k in by if '퍼스널 데이터' in by[k]['before'] and k.startswith('DT_Tips|Single_Character|')]),
    ('⑮', '시스템 메시지의 あなた', '검수 안: 문장 앞 「당신은」은 빼고, 「당신의 클랜」은 「우리 클랜」. 「우리 클랜」은 시스템이 플레이어 편처럼 말하는 꼴이라 「소속 클랜」·「클랜」 후보',
     [k for k in by if '8-2' in str(by[k]['rule']) and by[k]['chunk'] == 'F_messagebox']),
    ('⑭', '고정 줄 고칠 제안 7건', '「괜찮습니까?」 통일 등으로 고정한 줄 안의 다른 표현: 「당신은」 2줄, 「소거」, 「#State#의 요새」 5줄, 「동반하는」, EB_08 「의도 → 목적」',
     ['DT_UI_MessageBox|Messages_Confirm|ConfirmResignGeneral', 'DT_UI_MessageBox|Messages_Confirm|ConfirmClanApplication',
      'DT_UI_MessageBox|Messages_Confirm|ConfirmResetData_02', 'DT_UI_MessageBox|Messages_Confirm|ConfirmSellFortress',
      'DT_UI_MessageBox|Messages_Confirm|ConfirmChangeHair', 'DT_CollectItems|Descriptions|EB_08']),
]
dec_of = {}
for no, title, desc, keys in DECIDE:
    for k in keys:
        dec_of.setdefault(k, no)


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


def ctx(jp, a, b):
    la, lb, lj = a.split('\n'), b.split('\n'), jp.split('\n')
    if len(la) <= 6 or len(la) != len(lb):
        return jp, a, b, ''
    ch = [i for i in range(len(la)) if la[i] != lb[i]]
    keep = sorted({j for i in ch for j in range(max(0, i - 1), min(len(la), i + 2))})
    pick = lambda L: '\n'.join(L[j] if j < len(L) else '' for j in keep)
    return pick(lj) if len(lj) == len(la) else jp, pick(la), pick(lb), '(긴 글이라 바뀐 줄 근처만)'


CSS = '''
:root{--bg:#fff;--fg:#1d1d1f;--mut:#6e6e73;--line:#e3e3e8;--del:#ffe1e1;--ins:#d9f5df;--hd:#f5f5f7;--acc:#b42318}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#1c1c1e;--fg:#f2f2f7;--mut:#a1a1a6;--line:#38383a;--del:#5a2323;--ins:#1f4a2a;--hd:#2c2c2e;--acc:#ff6b5b}}
body{background:var(--bg);color:var(--fg);font:14px/1.55 "Malgun Gothic",system-ui,sans-serif;margin:0;padding:16px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 4px;color:var(--acc)}h3{font-size:14px;margin:18px 0 4px}p.d{color:var(--mut);margin:0 0 8px}
table{border-collapse:collapse;width:100%;table-layout:fixed;min-width:900px}td,th{border:1px solid var(--line);padding:6px 8px;vertical-align:top;overflow-wrap:anywhere}
th{background:var(--hd);text-align:left}td.n{width:40px;text-align:right;color:var(--mut)}
del{background:var(--del);text-decoration:line-through}ins{background:var(--ins);text-decoration:none}
.k{font-size:11px;color:var(--mut)}.why{font-size:12.5px}.note{font-size:12.5px;color:var(--acc);margin-top:4px}.wrap{overflow-x:auto}
'''
out = ['<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       '<title>데빌즈 서드 재검수 대조표</title><style>%s</style></head><body>' % CSS]
out.append('<h1>데빌즈 서드 새 번역 규칙 재검수 대조표</h1><p class="d">검수 담당 9명 고칠 안 %d건. 빨강 = 지울 글자, 초록 = 넣을 글자. '
           '「제안」 칸이 반영할 글. 「규칙」은 jp-translationese-rules 장 번호.</p>' % len(items))
n = 0


def table(rows):
    global n
    out.append('<div class="wrap"><table><colgroup><col style="width:40px"><col style="width:22%"><col style="width:24%">'
               '<col style="width:24%"><col></colgroup><tr><th>#</th><th>원문</th><th>수정 전</th><th>제안</th><th>규칙·이유</th></tr>')
    for x in rows:
        n += 1
        x['no'] = n
        jp, a, b, c = ctx(src[x['key']]['jp'], x['before'], x['proposal'])
        da, db = diff(a, b)
        same = '<div class="note">→ 바꾸지 않음(지금 그대로)</div>' if x['proposal'] == x['before'] else ''
        out.append('<tr><td class="n">%d</td><td>%s<div class="k">%s · %s %s</div></td><td>%s</td><td>%s%s</td><td class="why"><b>%s·%s</b> %s%s</td></tr>' % (
            n, html.escape(jp).replace('\n', '<br>'), html.escape(x['key']), html.escape(str(src[x['key']].get('speaker') or '-')), c,
            da, db, same, html.escape(x['severity']), html.escape(str(x['rule'])), html.escape(x['reason']),
            ('<div class="note">내 판단: %s</div>' % html.escape(x['note'])) if x['note'] else ''))
    out.append('</table></div>')


out.append('<h2>정해 줘 (%d묶음)</h2><p class="d">아래 줄들은 결정에 따라 바뀜. 검수 안이 있는 줄은 그 안을, 없는 줄은 지금 번역을 보여 줌.</p>' % len(DECIDE))
for no, title, desc, keys in DECIDE:
    out.append('<h3>%s %s</h3><p class="d">%s</p>' % (no, html.escape(title), html.escape(desc)))
    rows = []
    for k in keys:
        if k in by:
            rows.append(by[k])
        else:
            rows.append({'key': k, 'before': ko[k], 'proposal': ko[k], 'after': ko[k], 'severity': '-', 'rule': '-',
                         'reason': '검수 안 없음(물어볼 것만)', 'note': '', 'chunk': '-'})
    table(rows)
out.append('<h2>내가 검수 안을 바꾼 것</h2>')
table([by[k] for k in sorted(MINE)])
rest = [x for x in items if x['key'] not in dec_of and x['key'] not in MINE]
for sev in ('높음', '보통', '낮음'):
    rows = [x for x in rest if x['severity'] == sev]
    out.append('<h2>%s (%d건, 그대로 반영 권장)</h2>' % (sev, len(rows)))
    for ch in sorted({x['chunk'] for x in rows}):
        out.append('<h3>%s</h3>' % ch)
        table([x for x in rows if x['chunk'] == ch])
out.append('</body></html>')
open(os.path.join(W, '재검수_대조표.html'), 'w', encoding='utf-8').write('\n'.join(out))
json.dump([{k: x.get(k) for k in ('no', 'key', 'chunk', 'before', 'after', 'proposal', 'severity', 'rule')} | {'decide': dec_of.get(x['key'])}
           for x in items], open(os.path.join(W, 'proposals.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('제안', len(items), '결정 묶음', len(DECIDE), '결정 관련 키', len(dec_of), '그대로 반영 권장', len(rest))
for no, title, desc, keys in DECIDE:
    print(no, title, len(keys), '줄', '검수안 있음' if any(k in by for k in keys) else '검수안 없음')
