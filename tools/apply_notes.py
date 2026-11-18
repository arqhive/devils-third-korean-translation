"""질문거리 사용자 결정 반영(2026-11-06). 덩어리 파일을 직접 고친다.
실기 확인으로 정한 칸(폭 한도를 조금 넘지만 원문 낱말을 두고 실기에서 보기로 한 칸)은
work/translation/width_exceptions.json 에 적어 검사 도구가 폭 넘침을 문제로 치지 않게 한다.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OD = os.path.join(ROOT, 'work', 'translation', 'out')

SET = {
    'DT_Chapter_02|Subs_R190|L_013': '이봐, 네 눈은 옹이구멍이냐?',
    'DT_CollectItems|Labels|EB_06': 'SOD 부대',
    'DT_CollectItems|Labels|LQ_09': '마조',
    'DT_Game_Generic|ButtonLabels|ConfirmButton': '확인',
    'UnlockGore|Menus|Gore': '잔혹 표현',
    'UnlockGore|Menus|Disabled': '없음',
    'UnlockGore|Menus|Enabled': '있음',
    'DT_UI_Labels|Param_Labels|BaseWins': '방위',
    'DT_UI_Pause|Menus|Enbaku': '엔바쿠 발동',
    'DT_UI_Pause|Menus|Score': '스코어 표시',
    'DT_Weapons|NormalWeapons|Id_230': 'C4 폭탄',
    'DT_Weapons|Ammo_Labels|NoAmmo': '잔탄 없음',
    'DT_Weapons|Ammo_Labels|FullAmmo': '탄약 가득',
}
REPLACE = [
    ('DT_Chapter_03|Subs_R140|L_003', '역시 이반이라', '역시 러시아인이라'),
    ('DT_CollectItems|Descriptions|SV_04', '다른 이름으로 땡땡\n전차라고도 불리며,', '다른 이름으로 땡땡이\n라고도 불리며,'),
    ('DT_UI_MessageBox|Messages|AlreadyPurchased', '하티즈', '해티즈'),
]
# 실기에서 칸을 확인할 칸(폭 예외 + 확인 목록)
CHECK_IN_GAME = ['DT_Game_Generic|ButtonLabels|ConfirmButton', 'UnlockGore|Menus|Gore', 'UnlockGore|Menus|Disabled',
                 'UnlockGore|Menus|Enabled', 'DT_UI_Pause|Menus|Enbaku', 'DT_UI_Pause|Menus|Score',
                 'DT_Weapons|NormalWeapons|Id_230', 'DT_Weapons|Ammo_Labels|NoAmmo', 'DT_Weapons|Ammo_Labels|FullAmmo',
                 'DT_CollectItems|Labels|LQ_06', 'DT_CollectItems|Labels|LQ_09']


def main():
    src = {r['key']: r for r in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))}
    done = []
    for f in sorted(os.listdir(OD)):
        if not f.endswith('.json') or f.endswith('.notes.json'):
            continue
        p = os.path.join(OD, f)
        d = json.load(open(p, encoding='utf-8'))
        ch = False
        for k in list(d):
            old = d[k]
            if k in SET:
                d[k] = SET[k]
            for kk, a, b in REPLACE:
                if k == kk:
                    assert a in d[k], (k, a)
                    d[k] = d[k].replace(a, b)
            # よろしいですか → 「괜찮습니까?」로 통일
            if 'よろしいですか' in src[k]['jp']:
                d[k] = d[k].replace('괜찮으시겠습니까?', '괜찮습니까?').replace('괜찮겠습니까?', '괜찮습니까?')
            if d[k] != old:
                ch = True
                done.append('%s\n  전 %s\n  후 %s' % (k, old.replace('\n', '/'), d[k].replace('\n', '/')))
        if ch:
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(CHECK_IN_GAME, open(os.path.join(ROOT, 'work', 'translation', 'width_exceptions.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    open(os.path.join(ROOT, 'work', 'survey', 'notes_applied.txt'), 'w', encoding='utf-8').write('\n'.join(done))
    print('바뀐 줄', len(done))


if __name__ == '__main__':
    main()
