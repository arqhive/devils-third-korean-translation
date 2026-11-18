"""이름·직책·용어를 영어판(영어 음성) 기준으로(2026-11-18 사용자 지시 「영어 음성 기준으로 할거니까 직책 같은 것도 다 영어판 기준으로」).

사용자 결정(11/18): 아이반 → 이반, グレネード → 수류탄(Grenade), イエス サー → 「알겠습니다!」(Yes, sir).
영어판 표기를 따른 것: 장관 → 국장(Caraway, acting director of the NDI), 델타 대장(Captain) → 대위,
  중장(조종사가 캐러웨이에게, Admiral) → 제독, Copy that 2줄 「라저」 → 「알았다」, 코르치크 → 카시탄(Kashtan),
  류드밀라의 아버님 → 쿠마노(Kumano, 「father Kumano」 줄은 그대로),
  자막 이름표 Osprey Pilot·US Soldier·Giant Chimera Golem.
그대로(11/18 사용자 결정): Roger 는 「라저」(「보통 이렇게 쓰니께」), 데브그루.
그대로: 골드 팀 대장·이름표 「대장」(Soldier Leader)·제니트 「대장급」·쿠마노 「퇴역 중장」(영어 칸 비어 있음).

사용: python -I -X utf8 tools/term_en.py          → 조회만(work/review3/영어용어_대조표.html, 개수)
      python -I -X utf8 tools/term_en.py --apply  → 덩어리 번역(work/translation/out)에 넣음
"""
import collections
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
W = os.path.join(ROOT, 'work', 'review3')

GLOBAL = [('아이반', '이반')]  # 받침 같음(ㄴ) → 조사 그대로

EDITS = {
    # グレネード → 수류탄 (받침 생김: 조사까지 줄마다 지정)
    'DT_Chapter_02|Subs_R310|L_008': [('그레네이드!', '수류탄!')],
    'DT_Chapter_03|Subs_R000|L_014': [('그레네이드!', '수류탄!')],
    'DT_Chapter_03|Subs_R000|L_015': [('그레네이드!', '수류탄!')],
    'DT_Chapter_09|Subs_R000|L_018': [('그레네이드!', '수류탄!')],
    'DT_CollectItems|Descriptions|ST_07': [('소총과 그레네이드 등', '소총과 수류탄 등')],
    'DT_UI_Pause|Menus|grenade': [('그레네이드', '수류탄')],
    'DT_Weapons|AmmoBox|AMMOBOX_GRENADE': [('그레네이드 상자', '수류탄 상자')],
    'DT_Weapons|NormalWeapons|Id_59': [('프래그 그레네이드', '세열 수류탄')],
    'DT_Weapons|NormalWeapons|Id_60': [('스모크 그레네이드', '연막 수류탄')],
    'DT_Weapons|NormalWeapons|Id_61': [('스턴 그레네이드', '섬광 수류탄')],
    'DT_Weapons|NormalWeapons|Id_62': [('레이더 그레네이드', '레이더 수류탄')],
    'DT_Weapons|NormalWeapons|Id_63': [('센서 그레네이드', '센서 수류탄')],
    'DT_Weapons|NormalWeapons|Id_64': [('가스 그레네이드', '가스 수류탄')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_51': [('그레네이드 런처', '유탄 발사기'), ('그레네이드탄을', '유탄을')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_52': [('그레네이드 런처', '유탄 발사기'), ('그레네이드탄을', '유탄을')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_62': [('그레네이드처럼', '수류탄처럼')],
    'DT_Tips|Multi_Single|Arm_06': [('프래그 그레네이드는', '세열 수류탄은')],
    # イエス サー → 알겠습니다!
    'DT_Chapter_07|Subs_C110|L_009': [('예스 서!', '알겠습니다!')],
    'DT_Chapter_07|Subs_C110|L_010': [('예스 서!', '알겠습니다!')],
    'DT_Chapter_07|Subs_C110|L_011': [('예스 서!', '알겠습니다!')],
    'DT_Chapter_08|Subs_R050|L_011': [('예스 서!', '알겠습니다!')],
    # 長官 → 국장 (영어 Caraway / acting director of the NDI)
    'DT_Chapter_08|Subs_C030|L_003': [('캐러웨이 장관이야', '캐러웨이 국장이야')],
    'DT_Chapter_08|Subs_C040|L_005': [('장관이 데려온', '국장이 데려온')],
    'DT_Chapter_08|Subs_R060|L_003': [('장관이 이끄는', '국장이 이끄는')],
    'DT_Tips|Single_Character|Caraway_01': [('NDI의 장관이다', 'NDI의 국장 대행이다')],
    # 델타 隊長(Captain, 밥) → 대위
    'DT_Chapter_02|Subs_C040|L_001': [('대장하고는', '대위하고는')],
    'DT_Chapter_03|Subs_C050|L_002': [('대장님', '대위님')],
    'DT_Chapter_04|Subs_R130|L_001': [('대장님', '대위님')],
    'DT_Chapter_04|Subs_R190|L_001': [('대장님', '대위님')],
    'DT_Chapter_05|Subs_C032|L_006': [('대장님', '대위님')],
    'DT_Chapter_05|Subs_C070|L_003': [('대장.', '대위.')],
    'DT_Chapter_07|Subs_R010|L_006': [('대장님', '대위님')],
    'DT_Chapter_07|Subs_R010|L_008': [('대장님은', '대위님은')],
    'DT_Chapter_07|Subs_R010|L_009': [('대장님을', '대위님을')],
    'DT_Chapter_07|Subs_R010|L_010': [('대장님', '대위님')],
    'DT_Chapter_07_Mg1|Subs_Set07|L_002': [('대장님', '대위님')],
    # 中将(조종사 → 캐러웨이, Admiral) → 제독
    'DT_Chapter_08|Subs_R050|L_004': [('중장님', '제독님')],
    # ラジャー: Roger 는 「라저」 그대로, Copy that 2줄만 「알았다」
    'DT_Chapter_02|Subs_R050|L_002': [('라저.', '알았다.')],
    'DT_Chapter_03|Subs_R010|L_002': [('라저!', '알았다!')],
    # コールチク → 카시탄(Kashtan)
    'DT_Chapter_08|Subs_C077|L_001': [('코르치크', '카시탄')],
    'DT_Chapter_08|Subs_R070|L_004': [('코르치크로', '카시탄으로')],
    'DT_Chapter_08|Subs_R080|L_001': [('코르치크를', '카시탄을')],
    'DT_Chapter_08|Subs_R080|L_003': [('코르치크를', '카시탄을')],
    'DT_Chapter_08|Subs_R080|L_007': [('코르치크를', '카시탄을')],
    # お父様(류드밀라) → 쿠마노(영어 Kumano). 「father Kumano」 줄(C110 L_018)은 그대로
    'DT_Chapter_09|Subs_C070|L_009': [('아버님의', '쿠마노의')],
    'DT_Chapter_09|Subs_C080|L_004': [('아버님을', '쿠마노를')],
    'DT_Chapter_09|Subs_C110|L_009': [('아버님은 옳았다', '쿠마노가 옳았다')],
    # 자막 이름표(영어판 이름표)
    'DT_Game_Generic|CharacterName_Subs|OspreyPilot': [('조종사', '오스프리 조종사')],
    'DT_Game_Generic|CharacterName_Subs|USSoldierA': [('오퍼레이터', '미군 병사')],
    'DT_Game_Generic|CharacterName_Subs|GiantChimeraGolem': [('키메라 골렘', '자이언트 키메라 골렘')],
}


def build(ko):
    rows = []
    for k, v in ko.items():
        a = v
        why = []
        for old, new in EDITS.get(k, []):
            n = a.count(old)
            assert n >= 1, (k, old)
            a = a.replace(old, new)
            why.append('%s→%s' % (old, new))
        for old, new in GLOBAL:
            if old in a:
                a = a.replace(old, new)
                why.append('%s→%s' % (old, new))
        if a != v:
            rows.append((k, v, a, ', '.join(why)))
    assert set(EDITS) <= {r[0] for r in rows}
    return rows


def main():
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    rows = build(ko)
    c = collections.Counter('이름(아이반→이반)만' if r[3] == '아이반→이반' else '용어·직책' for r in rows)
    print('바뀌는 줄', len(rows), dict(c))
    left = {w: sum(w in r[2] for r in rows) + sum(w in v for k, v in ko.items() if k not in {r[0] for r in rows})
            for w in ('아이반', '그레네이드', '예스 서', '코르치크', '로저', 'DEVGRU')}
    print('남는 옛 표기', left)
    if '--apply' in sys.argv:
        want = {k: (b, a) for k, b, a, _ in rows}
        hit = set()
        for f in sorted(os.listdir(OD)):
            if not f.endswith('.json') or f.endswith('.notes.json'):
                continue
            p = os.path.join(OD, f)
            d = json.load(open(p, encoding='utf-8'))
            chg = False
            for key in d:
                if key in want:
                    assert d[key] == want[key][0], key
                    d[key] = want[key][1]
                    hit.add(key)
                    chg = True
            if chg:
                json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        assert hit == set(want)
        print('반영', len(hit))
        return
    src = {}
    for f in os.listdir(os.path.join(ROOT, 'work', 'translation', 'src')):
        for r in json.load(open(os.path.join(ROOT, 'work', 'translation', 'src', f), encoding='utf-8')):
            src[r['key']] = r
    out = ['<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>영어판 용어 대조표</title><style>body{font:14px/1.55 "Malgun Gothic",sans-serif;margin:16px;background:#fff;color:#1d1d1f}'
           '@media (prefers-color-scheme: dark){body{background:#1c1c1e;color:#f2f2f7}}'
           'table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;vertical-align:top}.k{font-size:11px;color:#888}</style>'
           '</head><body><h1>이름·직책·용어 영어판 기준 대조표</h1><p>' + html.escape(json.dumps(dict(c), ensure_ascii=False)) +
           ' — 「아이반→이반」만 바뀌는 줄은 맨 아래에 모음</p><table><tr><th>#</th><th>키</th><th>영어</th><th>수정 전</th><th>수정 후</th><th>바꾼 것</th></tr>']
    rows.sort(key=lambda r: r[3] == '아이반→이반')
    for i, (k, b, a, w) in enumerate(rows, 1):
        en = (src.get(k, {}).get('en') or '')
        cut = lambda s: html.escape(s if len(s) < 400 else s[:400] + '…').replace('\n', '<br>')
        out.append('<tr><td>%d</td><td class="k">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            i, html.escape(k), cut(en), cut(b), cut(a), html.escape(w)))
    out.append('</table></body></html>')
    open(os.path.join(W, '영어용어_대조표.html'), 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
