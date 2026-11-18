"""용어마다 북미판(INT) 표기 찾기: 일본어 원문에 용어가 든 키의 INT 값에서 후보 영어 낱말이 나오는지 센다.

입력 표: [(일본어 용어, [영어 후보 정규식…])]
출력: work/survey/na_names.txt  (용어, 일본어 등장 수, 후보별 INT 등장 수, 예문)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERMS = [
    ('アイヴァン', [r'Ivan']), ('イヴァン', [r'Ivan the Terrible', r'Ivan']), ('キャラウェイ', [r'Caraway']),
    ('長官', [r'Director', r'Secretary', r'Caraway', r'Chief']), ('ステラ', [r'Stella']), ('メイナード', [r'Maynard']),
    ('ボブ', [r'Bob']), ('隊長', [r'Captain', r'Cap\b', r'Sir', r'Chief']), ('クマノ', [r'Kumano']), ('アイザック', [r'Isaac']),
    ('リュドミラ', [r'Ludmilla', r'Lyudmila']), ('カレーニナ', [r'Karenina']), ('ジェーン', [r'Jane']), ('ビッグマウス', [r'Big Mouse', r'Bigmouse']),
    ('シャハ', [r'Saha', r'Shah']), ('グルンドラ', [r'Grundla', r'Grundra']), ('前田', [r'Maeda']), ('モロトフ', [r'Molotov']),
    ('カニンガム', [r'Cunningham']), ('デブグル', [r'DEVGRU', r'DevGru']), ('ゼニート', [r'Zenit']),
    ('スタールイ', [r'Staryi', r'Stary', r'Braat Island', r'Braat']), ('ムラートシイ', [r'Mladshiy', r'Mladshi', r'Little Braat']),
    ('ブラート', [r'Braat']), ('ツアー', [r'Tsar Bell', r'Tsar', r'Czar']), ('ケスラー', [r'Kessler syndrome', r'Kessler Syndrome', r'Kessler']),
    ('コールチク', [r'Kashtan', r'Kortik']), ('クラブK', [r'Club-K', r'Club K']), ('スクール', [r'School of Democracy']),
    ('レニウム', [r'Rhenium']), ('エクソスーツ', [r'[Ee]xosuit', r'[Ee]xo-suit', r'EXO']), ('グラス', [r'[Gg]lass']),
    ('キメラ', [r'Chimera']), ('遺伝子改変薬', [r'transgenic', r'[Gg]enetic']), ('ビーコン弾', [r'tracking', r'beacon', r'[Tt]racer']),
    ('グレネード', [r'[Gg]renade']), ('ピースメーカー', [r'Peacemaker']), ('炎魄', [r'Enbaku', r'[Rr]age']),
    ('ラジャー', [r'Copy', r'Roger']), ('イエス サー', [r'Yes,? sir', r'Sir']), ('メレーショット', [r'Melee Shot']),
    ('フィニッシュブロー', [r'Finishing Blow']), ('テクニカルポイント', [r'Technical Point']), ('戦利品', [r'War Troph', r'[Tt]roph']),
    ('スコアアタック', [r'Score Attack']), ('ソロプレイ', [r'Solo-?play', r'Single']), ('グリーンベレー', [r'Green Beret']),
    ('ゴールドチーム', [r'Gold Team']), ('デルタ', [r'Delta']), ('無人攻撃機', [r'drone', r'UAV', r'UCAV']),
    ('エイムアタック', [r'Aim Attack']), ('ターゲットアシスト', [r'Aim Assist', r'Target Assist']),
    ('C4', [r'C4']), ('SOD', [r'SOD']), ('グアンタナモ', [r'Guantanamo']), ('パナマ', [r'Panama']),
]


def main():
    r = [x for x in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
         if x['scope'] == 'solo']
    out = []
    for jp, cands in TERMS:
        xs = [x for x in r if jp in x['jp']]
        withen = [x for x in xs if x.get('en')]
        cnt = []
        for c in cands:
            n = sum(1 for x in withen if re.search(c, x['en']))
            cnt.append('%s=%d' % (c, n))
        ex = ''
        for c in cands:
            hit = [x for x in withen if re.search(c, x['en'])]
            if hit:
                ex = hit[0]['en'].replace('\n', ' / ')[:90]
                break
        if not ex and withen:
            ex = '(후보 없음) ' + withen[0]['en'].replace('\n', ' / ')[:90]
        out.append('%s\t일본어 %d(영어 있음 %d)\t%s\t%s' % (jp, len(xs), len(withen), ' '.join(cnt), ex))
    open(os.path.join(ROOT, 'work', 'survey', 'na_names.txt'), 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
