"""새 번역 규칙 재검수 반영 2단계(2026-11-17 사용자 결정 ⑧⑨⑩⑫⑭).

사용: python -I -X utf8 tools/apply_review2_step2.py          → 조회만(대조표 work/review2/2단계_대조표.html)
      python -I -X utf8 tools/apply_review2_step2.py --apply  → 덩어리 번역(work/translation/out)에 넣음
"""
import difflib
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
W = os.path.join(ROOT, 'work', 'review2')
src = {r['key']: r for r in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))}
ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
props = {x['key']: x for x in json.load(open(os.path.join(W, 'proposals.json'), encoding='utf-8'))}

# (결정, 키, [(바꿀 글, 새 글), ...]) — 바꿀 글은 그 줄에 정확히 있어야 함(개수 확인)
EDITS = [
    ('⑧', 'DT_CollectItems|Descriptions|EB_07', [('스텔스 미채 장갑', '스텔스 위장 장갑')]),
    ('⑨', 'DT_CollectItems|Descriptions|LQ_06', [('일본주', '사케')]),
    ('⑨', 'DT_CollectItems|Descriptions|LQ_09', [('일본주', '사케')]),
    ('⑩', 'DT_UI_MessageBox|Messages|DonationTax', [('헌금액', '기부액')]),
    ('⑩', 'DT_UI_MessageBox|Messages|OfferingToClan', [('헌금했습니다', '기부했습니다')]),
    ('⑩', 'DT_UI_MessageBox|Messages_Error|ErrorOverDollenAmount', [('헌금할', '기부할')]),
    ('⑩', 'DT_UI_MessageBox|Messages_Error|ErrorDonate', [('헌금은', '기부는')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmResignGeneral', [('당신은 일반', '일반')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmClanApplication', [('때까지 당신은 용병이', '때까지 용병이')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmResetData_02', [('소거된', '삭제된')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmSellFortress', [('#State#의 요새', '#State# 요새')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmBuyFortress', [('#State#의 요새', '#State# 요새')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmUpgradeFortress', [('#State#의 요새', '#State# 요새')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmProtectFortress', [('#State#의 요새', '#State# 요새')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmCustomize', [('#State#의 요새', '#State# 요새')]),
    ('⑭', 'DT_UI_MessageBox|Messages_Confirm|ConfirmChangeHair', [('성별 변경을 동반하는 얼굴 변경을', '성별까지 바뀌는 얼굴 변경을')]),
    ('⑭', 'DT_CollectItems|Descriptions|EB_08', [('의도는 같지만', '목적은 같지만')]),
]
# ⑫ 무기 설명 「나라+의+회사사」 → 「나라 회사사」(회사가 아닌 「개발사(역사)」는 뺌)
PAT = re.compile(r'([가-힣]+)의 ((?:[A-Z0-9가-힣&.\-]+ )?[A-Z가-힣0-9&.\-]*사)(?=가|는|의|에서|와|를|이|도)')
for k, v in ko.items():
    if not k.startswith('DT_Weapons|NormalWeapons_Descriptions|'):
        continue
    pairs = [(m.group(0), '%s %s' % (m.group(1), m.group(2))) for m in PAT.finditer(v)]
    if pairs:
        EDITS.append(('⑫', k, pairs))


def build():
    rows = []
    for dec, k, pairs in EDITS:
        before = ko[k]
        after = before
        if dec == '⑨' and k in props and props[k]['proposal'] != props[k]['before']:
            # 1단계에서 미룬 검수 안(LQ_09 는 이미 「일본주→사케」만) — 검수 안을 먼저 얹고 일본주 바꿈
            assert props[k]['before'] == before, k
            after = props[k]['proposal']
        for a, b in pairs:
            n = after.count(a)
            if n == 0 and dec == '⑨' and b in after:
                continue  # 검수 안에 이미 들어 있음(LQ_09)
            assert n >= 1, (k, a)
            after = after.replace(a, b)
        rows.append((dec, k, before, after))
    return rows


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


def main():
    rows = build()
    if '--apply' in sys.argv:
        want = {k: (b, a) for _, k, b, a in rows}
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
        return
    out = ['<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>재검수 2단계 대조표</title><style>body{font:14px/1.55 "Malgun Gothic",sans-serif;margin:16px;background:#fff;color:#1d1d1f}'
           '@media (prefers-color-scheme: dark){body{background:#1c1c1e;color:#f2f2f7}}'
           'table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;vertical-align:top}'
           'del{background:#ffdede}ins{background:#d9f5df;text-decoration:none}.k{font-size:11px;color:#888}</style></head><body>'
           '<h1>재검수 2단계 대조표</h1><p>결정 ⑧ 미채 · ⑨ 사케 · ⑩ 기부 · ⑫ 「나라 회사」 · ⑭ 고정 줄. 빨강 = 지울 글자, 초록 = 넣을 글자.</p>'
           '<table><tr><th>#</th><th>결정</th><th>원문</th><th>수정 전</th><th>수정 후</th></tr>']
    for i, (dec, k, b, a) in enumerate(rows, 1):
        db, da = diff(b, a)
        out.append('<tr><td>%d</td><td>%s</td><td>%s<div class="k">%s</div></td><td>%s</td><td>%s</td></tr>' % (
            i, dec, html.escape(src[k]['jp']).replace('\n', '<br>'), html.escape(k), db, da))
    out.append('</table></body></html>')
    open(os.path.join(W, '2단계_대조표.html'), 'w', encoding='utf-8').write('\n'.join(out))
    import collections
    print('대상 줄', len(rows), dict(collections.Counter(r[0] for r in rows)))
    # 검사용 사본
    tmp = dict(ko)
    for _, k, b, a in rows:
        tmp[k] = a
    json.dump(tmp, open(os.path.join(W, '_ko_step2.json'), 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
