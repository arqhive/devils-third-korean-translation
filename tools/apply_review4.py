"""모든 번역 영어 기준 재번역 반영(2026-11-18 사용자 「모든 번역 영어기준으로」).

work/review4/changes.json(담당 10명 결과 중 바뀐 줄, tools/review3_table.py review4 가 만듦) + 내 검수 고침(FIX)
→ 덩어리 번역(work/translation/out)에 넣음.
사용: python -I -X utf8 tools/apply_review4.py           → 조회만(work/review4/changes_final.json)
      python -I -X utf8 tools/apply_review4.py --apply   → 넣기
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
W = os.path.join(ROOT, 'work', 'review4')

# 내 검수: 키 → 새 글(None = 지금 번역 유지)
FIX = {
    # 스텔라 편한 반말(사용자 결정) — 국장에게 하는 보고도 반말로
    'DT_Chapter_03|Subs_C010|L_004': '이미 신호 추적 중이야.\n브라트 경제특구로 향하는 것 같아.',
    'DT_Chapter_09|Subs_C120|L_002': 'C4 수술 끝났어.\n쿠마노의 혈청으로 키메라 바이러스도 다 없어졌어.',
    # 국장 하게체 남은 것
    'DT_Chapter_09|Subs_C020|L_002': '전 전투기, 즉시 인디펜던스로 귀환하라.\n폭격대는 스타리 브라트 공항으로 향하라.\n미첼은 불시착시켜도 상관없다.\n최대한 서둘러라. 알겠지?\n이상.',
    # 같은 영어(Battle is already running.) 세 줄 맞춤
    'DT_UI_MessageBox|Messages_Error|ErrorAlreadyRun': '전투가 이미 시작되었습니다.',
}


# 11/18 사용자 결정 4가지
FIX.update({
    # ② 光学迷彩 → 「광학 위장」으로 통일(받침 생김, 조사까지)
    'DT_Chapter_07|Subs_C076|L_007': '광학 위장?!',
    'DT_Chapter_07|Subs_R110|L_001': '광학 위장이다.',
    # ③ 술 이름은 고유 이름 유지: 라벨은 지금 번역 그대로
    'DT_CollectItems|Labels|LQ_01': None,
    'DT_CollectItems|Labels|LQ_04': None,
    'DT_CollectItems|Labels|LQ_05': None,
    'DT_CollectItems|Labels|LQ_06': None,
    'DT_CollectItems|Labels|LQ_07': None,
    # ④ 팁 버튼 표기 살림(영어 문장 + 버튼)
    'DT_Tips|Multi_Single|Action_04': '조준(ZL)을 누른 채 강한 공격(X)을 하면 들고 있는 무기를 던질 수 있다.',
    'DT_Tips|Multi_Single|Action_06': '무기를 들고 있지 않을 때는 A 버튼을 누르지 않아도 근처 바닥에 떨어진 무기를 자동으로 줍는다.',
    'DT_Tips|Multi_Single|Action_11': '적을 조준 고정(ZL)한 채 빠른 공격(Y)을 하면 / 강력한 조준 공격을 날린다.'.replace(' / ', '\n'),
    'DT_Tips|Multi_Single|Action_14': '방어 중에 L 스틱을 기울이면 회피한다(방어 + L 스틱).\n회피는 강한 적과 싸울 때 중요한 기술이다.',
    'DT_Tips|Multi_Single|Action_22': '방어가 단단한 적에게는 무기 던지기(ZL + X 버튼)가 효과적이다.',
    'DT_Tips|Multi_Single|Arm_04': '탄약이 떨어지기 전에 재장전 버튼(A)으로 탄창을 채워 두어라.',
    'DT_Tips|Single|Action_09': '조준 공격(ZL+Y)으로 적을 쓰러뜨리면\n엔바쿠 게이지가 많이 찬다.',
    'DT_Tips|Single|Action_10': '엔바쿠 게이지가 가득 차면 점프와 빠른 공격(Y+B)을 함께 눌러 힘을 해방하라.',
})


def extra(ko, final):
    """① 장 제목 영어판대로: 수집품 위치 라벨도 맞춤, ③ 마조 설명 「전설의」 → 「환상의」(사용자 결정 유지)."""
    out = {}
    titles = {'제정의 잔광': '제정 러시아의 잔재', '브라트 요시와라 고계행': '홍등가'}
    for k, v in ko.items():
        cur = final.get(k, (v, v))[1]
        new = cur
        if '|Locations|' in k:
            for a, b in titles.items():
                new = new.replace(a, b)
        if k == 'DT_CollectItems|Descriptions|LQ_09':
            new = new.replace('전설의', '환상의')
        if new != cur:
            out[k] = new
    return out


def main():
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    ch = json.load(open(os.path.join(W, 'changes.json'), encoding='utf-8'))
    final = {}
    for k, (b, a) in ch.items():
        assert ko[k] == b, k
        final[k] = (b, a)
    for k, v in FIX.items():
        b = ko[k]
        if v is None:
            final.pop(k, None)
        elif v != b:
            final[k] = (b, v)
    ex = extra(ko, final)
    print('사용자 결정으로 더 고친 줄(장 제목·마조)', len(ex))
    for k, v in ex.items():
        final[k] = (ko[k], v)
    json.dump(final, open(os.path.join(W, 'changes_final.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('담당 결과 바뀐 줄', len(ch), '내 고침', len(FIX), '최종', len(final))
    if '--apply' not in sys.argv:
        return
    hit = set()
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        chg = False
        for key in d:
            if key in final:
                assert d[key] == final[key][0], key
                d[key] = final[key][1]
                hit.add(key)
                chg = True
        if chg:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    assert hit == set(final)
    print('반영', len(hit))


if __name__ == '__main__':
    main()
