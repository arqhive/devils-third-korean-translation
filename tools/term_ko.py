"""외래어 게임 용어를 우리말로(2026-11-17 사용자 「리로드/인터랙트/바이브레이션 등 한국어로」, 추천안 승인).

용어: 리로드→재장전, 대시→달리기, 커버→엄폐(대사 cover me 는 엄호), 커버 어시스트→엄폐 보조, 타깃 어시스트→조준 보조,
에임→조준(에임 록→조준 고정), 밀리 샷→근접 사격, 피니시 블로→마무리 일격, 가드→방어, 어태치먼트→부착물, 대미지→피해,
테크니컬 포인트→기술 점수, 코스튬→의상, 리스폰→부활, 리셋→초기화, 매거진→탄창, 실드→방패, 어시스트(조작 보조)→보조
그대로: 앨범 커버, 문명의 리셋 스위치(비유), 닌텐도 e숍(이름), 점수 라벨 「어시스트」(킬 어시스트)
줄마다 (바꿀 글, 새 글)을 정확히 적는다(일괄 치환 아님).

사용: python -I -X utf8 tools/term_ko.py          → 조회(대조표 work/review2/용어_대조표.html, 검사용 사본)
      python -I -X utf8 tools/term_ko.py --apply  → 덩어리 번역에 넣음
"""
import difflib
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')
W = os.path.join(ROOT, 'work', 'review2')
src = {r['key']: r for r in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))}
ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
locked = json.load(open(os.path.join(W, 'locked.json'), encoding='utf-8'))

E = {
    # 재장전
    'DT_Tips|Multi_Single|Arm_01': [('리로드 중에', '재장전 중에')],
    'DT_Tips|Multi_Single|Arm_04': [('매거진에', '탄창에'), ('리로드할', '재장전할')],
    'DT_UI_Pause|Menus|Interact': [('리로드/', '재장전/')],
    'DT_UI_Tutorial|Subtitles|locMessages[19]': [('리로드', '재장전')],
    'DT_Weapons|Ammo_Labels|Reload': [('리로드', '재장전')],
    # 달리기
    'DT_Tips|Multi_Single|Action_13': [('달리는 중에도 대시한다.', '뛰는 중에도 달리기를 한다.'), ('대시 중에', '달리기 중에'),
                                       ('계속 대시한다.', '계속 달린다.')],
    'DT_Tips|Multi_Single|Action_15': [('대시 중에', '달리기 중에')],
    'DT_Tips|Multi_Single|Action_16': [('대시와 회피', '달리기와 회피')],
    'DT_UI_Pause|Menus|Dash': [('대시', '달리기')],
    'DT_UI_Tutorial|Subtitles|locMessages[9]': [('대시', '달리기')],
    'DT_UI_Tutorial|Subtitles|locMessages[23]': [('대시 점프', '달리기 점프')],
    # 엄폐·엄호(대사는 영어판 확인: 1장만 cover me)
    'DT_Chapter_01|Subs_R130|L_007': [('커버해!', '엄호해!')],
    'DT_Chapter_02|Subs_R040|L_003': [('커버해!', '엄폐해!')],
    'DT_Chapter_03|Subs_R020|L_004': [('커버!', '엄폐해!')],
    'DT_Chapter_04|Subs_R010|L_009': [('커버!', '엄폐해!')],
    'DT_Chapter_04|Subs_R020|L_001': [('커버에 들어가.', '엄폐해.')],
    'DT_Chapter_05|Subs_R110|L_003': [('커버!', '엄폐해!')],
    'DT_Chapter_05|Subs_R130|L_004': [('커버에서 떨어지지 마.', '엄폐물에서 떨어지지 마.')],
    'DT_Chapter_05|Subs_R150|L_006': [('커버에 들어가 줘.', '엄폐해 줘.')],
    'DT_Chapter_06|Subs_R020|L_011': [('커버!', '엄폐해!')],
    'DT_Chapter_06|Subs_R060|L_004': [('경사로 커버를', '경사로 엄폐물을')],
    'DT_Chapter_06|Subs_R070|L_001': [('커버가 부서졌다!', '엄폐물이 부서졌다!')],
    'DT_Chapter_06|Subs_R070|L_002': [('커버를 바꿔 가며', '엄폐물을 바꿔 가며')],
    'DT_Chapter_07|Subs_R050|L_001': [('커버!', '엄폐해!')],
    'DT_Chapter_07|Subs_R080|L_004': [('커버해!', '엄폐해!')],
    'DT_Tips|Multi_Single|Action_17': [('커버 어시스트가', '엄폐 보조가'), ('자동으로 커버로 전환한다.', '자동으로 엄폐한다.')],
    'DT_Tips|Single|Arm_02': [('커버가 부서져도', '엄폐물이 부서져도')],
    'DT_Tips|Single|Arm_03': [('부서지는 커버도', '부서지는 엄폐물도')],
    'DT_UI_Pause|Descriptions|Info_CoverAssist': [('커버 액션을', '엄폐 동작을'), ('어시스트 기능입니다.', '보조 기능입니다.')],
    'DT_UI_Pause|Menus|CoverAssist': [('커버 어시스트', '엄폐 보조')],
    'DT_UI_Tutorial|Subtitles|locMessages[25]': [('커버', '엄폐')],
    'DT_UI_Tutorial|Subtitles|locMessages[74]': [('커버 어시스트', '엄폐 보조')],
    # 조준
    'DT_Tips|Single|Arm_01': [('타깃 어시스트는', '조준 보조는')],
    'DT_UI_Pause|Menus|AimAssist': [('타깃 어시스트', '조준 보조')],
    'DT_UI_Pause|Descriptions|Info_AimAssist': [('어시스트 기능입니다.', '보조 기능입니다.')],
    'DT_Tips|Multi_Single|Action_11': [('에임 어택을', '조준 공격을')],
    'DT_Tips|Single|Action_09': [('에임 어택(ZL+Y)으로', '조준 공격(ZL+Y)으로')],
    'DT_Tips|Single|Mission_08': [('에임 어택으로', '조준 공격으로'), ('테크니컬 포인트 “에임 록 킬”', '기술 점수 “조준 고정 킬”')],
    'DT_UI_Labels|Param_Labels|AimLockKill': [('에임 록', '조준 고정')],
    'DT_UI_Pause|Menus|Aim': [('에임', '조준')],
    'DT_UI_Tutorial|Subtitles|locMessages[4]': [('에임 어택', '조준 공격')],
    'DT_UI_Tutorial|Subtitles|locMessages[12]': [('에임', '조준')],
    'DT_UI_Tutorial|Subtitles|locMessages[13]': [('에임 사격', '조준 사격')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_231': [('어태치먼트는', '부착물은'), ('에임 어시스트', '조준 보조')],
    # 근접 사격
    'DT_Tips|Multi_Single|Action_05': [('“밀리 샷”은', '“근접 사격”은')],
    'DT_Tips|Multi_Single|Action_22': [('가드가 단단한', '방어가 단단한'), ('밀리 샷(', '근접 사격(')],
    'DT_Tips|Single|Mission_09': [('테크니컬 포인트 “밀리 샷”', '기술 점수 “근접 사격”')],
    'DT_UI_Labels|Param_Labels|ThrowingKnife': [('밀리 샷', '근접 사격')],
    'DT_UI_Tutorial|Subtitles|locMessages[68]': [('밀리 샷', '근접 사격')],
    # 마무리 일격
    'DT_Tips|Single|Action_02': [('피니시 블로가', '마무리 일격이')],
    'DT_Tips|Single|Action_03': [('피니시 블로는', '마무리 일격은')],
    'DT_Tips|Single|Action_04': [('피니시 블로는', '마무리 일격은')],
    'DT_Tips|Single|mission_11': [('피니시 블로로', '마무리 일격으로'), ('테크니컬 포인트 “피니시 블로”', '기술 점수 “마무리 일격”')],
    'DT_UI_Labels|Param_Labels|FinishBlow': [('피니시 블로', '마무리 일격')],
    # 방어
    'DT_Chapter_03|Subs_R200|L_006': [('가드가', '방어가')],
    'DT_Chapter_06|Subs_R020|L_006': [('가드가', '방어가')],
    'DT_Tips|Multi_Single|Action_02': [('가드할 수 없다.', '방어할 수 없다.')],
    'DT_Tips|Multi_Single|Action_03': [('적의 가드를', '적의 방어를')],
    'DT_Tips|Multi_Single|Action_07': [('계속 가드하면', '계속 방어하면')],
    'DT_Tips|Multi_Single|Action_08': [('가드할 수 있다.', '방어할 수 있다.')],
    'DT_Tips|Multi_Single|Action_12': [('가드로는', '방어로는')],
    'DT_Tips|Multi_Single|Action_14': [('“가드 + L 스틱”', '“방어 + L 스틱”')],
    'DT_Tips|Multi_Single|Action_18': [('가드를 굳힌', '방어를 굳힌'), ('가드를 무너뜨려라', '방어를 무너뜨려라')],
    'DT_Tips|Single|Action_05': [('가드할 수 없는', '방어할 수 없는')],
    'DT_UI_Pause|Menus|Guard': [('가드/', '방어/')],
    'DT_UI_Tutorial|Subtitles|locMessages[26]': [('가드', '방어')],
    # 부착물
    'DT_ShootingRaqnge|DataWindow_Labels|NotAttached': [('어태치먼트를', '부착물을')],
    'DT_ShootingRaqnge|DataWindow_Labels|EquipWeapon': [('어태치먼트를', '부착물을')],
    'DT_UI_Labels|Param_Labels|Attachment': [('어태치먼트', '부착물')],
    'DT_UI_MessageBox|ErrorMessages|E_2002': [('이 어태치먼트는', '이 부착물은')],
    'DT_UI_Tutorial|Subtitles|locMessages[67]': [('어태치먼트', '부착물')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_17': [('어태치먼트도', '부착물도')],
    # 피해
    'DT_ShootingRaqnge|DataWindow_Labels|Damage': [('대미지:', '피해:')],
    'DT_Tips|Single|Enemy_11': [('큰 대미지를', '큰 피해를')],
    'DT_UI_MessageBox|ErrorMessages|E_511': [('대미지를 받지 않았습니다.', '피해를 입지 않았습니다.')],
    'DT_UI_MessageBox|ErrorMessages|E_601': [('대미지를 받지 않았습니다.', '피해를 입지 않았습니다.')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_59': [('대미지를 준다.', '피해를 준다.')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_64': [('대미지를 누적시킨다.', '피해를 누적시킨다.')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_65': [('대미지가 누적된다.', '피해가 누적된다.')],
    # 기술 점수
    'DT_Tips|Single|Mission_02': [('테크니컬 포인트는', '기술 점수는')],
    'DT_Tips|Single|Mission_03': [('테크니컬 포인트', '기술 점수')],
    'DT_Tips|Single|Mission_04': [('테크니컬 포인트', '기술 점수')],
    'DT_Tips|Single|Mission_05': [('테크니컬 포인트', '기술 점수')],
    'DT_Tips|Single|Mission_06': [('테크니컬 포인트', '기술 점수')],
    'DT_Tips|Single|Mission_07': [('테크니컬 포인트', '기술 점수')],
    'DT_Tips|Single|mission_10': [('테크니컬 포인트', '기술 점수')],
    # 의상
    'DT_UI_MessageBox|ErrorMessages|E_111': [('이 코스튬은', '이 의상은')],
    'DT_UI_MessageBox|ErrorMessages|E_112': [('이 코스튬은', '이 의상은')],
    'DT_UI_MessageBox|ErrorMessages|E_113': [('이 코스튬은', '이 의상은')],
    'DT_UI_MessageBox|ErrorMessages|E_143': [('이 코스튬은', '이 의상은')],
    'DT_UI_MessageBox|ErrorMessages|E_2403': [('카테고리의 코스튬이', '카테고리의 의상이')],
    'DT_UI_MessageBox|Messages|UnlockOutfit': [('코스튬이', '의상이')],
    'DT_UI_MessageBox|Messages|OutfitLocked': [('이 코스튬은', '이 의상은')],
    'DT_UI_MessageBox|Messages_Confirm|ConfirmPurchaseOutfit': [('이 코스튬을', '이 의상을')],
    'DT_UI_MessageBox|Messages_Confirm|ConfirmChangeGender': [('코스튬 파츠는', '의상 파츠는')],
    # 부활
    'DT_UI_MessageBox|Messages_Confirm|ConfirmRespawn': [('리스폰합니다.', '부활합니다.')],
    'DT_UI_Pause|Labels|SetRespawnPoint': [('리스폰 포인트를', '부활 지점을')],
    'DT_UI_Pause|Labels|RespawnTimeRemain': [('리스폰 지점', '부활 지점')],
    'DT_UI_Pause|Labels|RespawnCount': [('리스폰 타임', '부활 시간')],
    'DT_UI_Pause|Menus|Respawn': [('리스폰', '부활')],
    # 초기화
    'DT_UI_MessageBox|ErrorMessages|E_2601': [('리셋할 수 없습니다.', '초기화할 수 없습니다.')],
    'DT_UI_MessageBox|ErrorMessages|E_2602': [('이미 리셋되었습니다.', '이미 초기화되었습니다.')],
    'DT_UI_MessageBox|Messages|CharacterReset_02': [('캐릭터를 리셋할 수', '캐릭터를 초기화할 수')],
    'DT_UI_MessageBox|Messages|CharacterReset_03': [('리셋할 수 없습니다.', '초기화할 수 없습니다.')],
    'DT_UI_MessageBox|Messages|CharacterReset_04': [('플레이어를 리셋할 수', '플레이어를 초기화할 수')],
    'DT_UI_MessageBox|Messages_Confirm|ConfirmChangeArmamentType': [('리셋되지만', '초기화되지만')],
    # 탄창
    'DT_Weapons|NormalWeapons_Descriptions|Id_28': [('원통형 매거진을', '원통형 탄창을'), ('이 매거진은', '이 탄창은')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_30': [('매거진 교환에', '탄창 교환에')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_40': [('튜브 매거진을', '관형 탄창을')],
    'DT_Weapons|NormalWeapons_Descriptions|Id_50': [('롱 매거진이', '긴 탄창이')],
    # 방패
    'DT_Chapter_02|Subs_R000|L_002': [('방탄 실드를', '방탄 방패를')],
    'DT_Chapter_03|Subs_R200|L_003': [('방탄 실드를', '방탄 방패를')],
    'DT_Chapter_03|Subs_R200|L_007': [('저 실드를', '저 방패를')],
    'DT_Chapter_06|Subs_R020|L_003': [('방탄 실드를', '방탄 방패를')],
    'DT_Chapter_06|Subs_R020|L_007': [('저 실드를', '저 방패를')],
    'DT_Chapter_09|Subs_R000|L_002': [('방탄 실드를', '방탄 방패를')],
    'DT_Chapter_09|Subs_R000|L_004': [('저 실드를', '저 방패를')],
    'DT_Tips|Single|Enemy_02': [('실드병에게는', '방패병에게는')],
    # 보조
    'DT_Tips|Single_Character|Bob_03': [('파워 어시스트 슈트', '근력 보조 슈트')],
}


def rows():
    out = []
    for k, pairs in E.items():
        before = ko[k]
        after = before
        for a, b in pairs:
            assert after.count(a) == 1, (k, a, after.count(a))
            after = after.replace(a, b)
        out.append((k, before, after))
    return out


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
    rs = rows()
    if '--apply' in sys.argv:
        want = {k: (b, a) for k, b, a in rs}
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
           '<title>용어 우리말 대조표</title><style>body{font:14px/1.55 "Malgun Gothic",sans-serif;margin:16px;background:#fff;color:#1d1d1f}'
           '@media (prefers-color-scheme: dark){body{background:#1c1c1e;color:#f2f2f7}}'
           'table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;vertical-align:top}'
           'del{background:#ffdede}ins{background:#d9f5df;text-decoration:none}.k{font-size:11px;color:#888}.l{color:#b42318;font-size:12px}</style></head><body>'
           '<h1>외래어 게임 용어 → 우리말 대조표</h1><p>빨강 = 지울 글자, 초록 = 넣을 글자. 「고정 줄」은 네가 정한 부분(효과적 등)은 그대로 두고 용어만 바꿈.</p>'
           '<table><tr><th>#</th><th>원문</th><th>수정 전</th><th>수정 후</th></tr>']
    for i, (k, b, a) in enumerate(rs, 1):
        db, da = diff(b, a)
        lk = '<div class="l">고정 줄: %s</div>' % html.escape(locked[k]) if k in locked else ''
        out.append('<tr><td>%d</td><td>%s<div class="k">%s</div>%s</td><td>%s</td><td>%s</td></tr>' % (
            i, html.escape(src[k]['jp']).replace('\n', '<br>'), html.escape(k), lk, db, da))
    out.append('</table></body></html>')
    open(os.path.join(W, '용어_대조표.html'), 'w', encoding='utf-8').write('\n'.join(out))
    tmp = dict(ko)
    for k, b, a in rs:
        tmp[k] = a
    json.dump(tmp, open(os.path.join(W, '_ko_terms.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('대상 줄', len(rs), '고정 줄', sum(1 for k, _, _ in rs if k in locked))


if __name__ == '__main__':
    main()
