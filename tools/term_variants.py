"""같은 원문 용어가 덩어리마다 다르게 번역됐는지 찾는다.
용어마다 한국어 후보를 주고, 그 용어가 든 줄에서 어떤 후보가 쓰였는지 덩어리별로 센다. 장 제목은 장 Settings 와 수집품 장소를 맞대 본다.
출력: work/survey/term_variants.txt
"""
import collections
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERMS = [
    ('ドレン', ['드렌', '도렌', '돌렌']), ('修復', ['수리', '수복', '복구']), ('エリア', ['에어리어', '지역', '구역', '에리어']),
    ('金の卵', ['금의 알', '황금알', '황금 알', '금알']), ('要塞攻略戦', ['요새 공략전', '요새공략전']),
    ('支援兵器', ['지원 병기', '지원병기', '지원 무기']), ('ドクロ勲章', ['해골 훈장']), ('勲章', ['훈장', '메달']),
    ('ベースキャンプ', ['베이스캠프', '베이스 캠프']), ('ゾーン', ['존', '구역']), ('クラン', ['클랜']),
    ('大尉', ['대위']), ('隊長', ['대장님', '대장', '팀장']), ('少佐', ['소령님', '소령']), ('長官', ['장관']),
    ('現地時間', ['현지 시간', '현지시간', '현지 시각', '현지시각']), ('日米露', ['일미러', '미일러', '미일러', '일미러']),
    ('苦界行', ['고계행', '고해행']), ('戦利品', ['전리품']), ('スコアアタック', ['스코어 어택', '스코어어택']),
    ('ミッション', ['미션', '임무']), ('レニウム', ['레늄']), ('キメラ', ['키메라']), ('遺伝子改変薬', ['유전자 변형 약', '유전자 변형약', '유전자변형약']),
    ('セーブ', ['저장', '세이브']), ('エンブレム', ['엠블럼', '엠블렘']), ('ミサイル', ['미사일']), ('カモフラージュ', ['카무플라주', '위장']),
    ('グリーンベレー', ['그린베레', '그린 베레']), ('ゴールドチーム', ['골드 팀', '골드팀']), ('デルタ', ['델타']),
    ('エクソスーツ', ['엑소슈트', '엑소 슈트']), ('無人攻撃機', ['무인 공격기', '무인공격기', '드론']), ('ビッグマウス', ['빅 마우스', '빅마우스']),
    ('ジェーン', ['제인']), ('ゼニート', ['제니트']), ('ブラート', ['브라트']), ('テクニカルポイント', ['테크니컬 포인트']),
    ('ターゲットアシスト', ['타깃 어시스트']), ('エイムアシスト', ['에임 어시스트']), ('ラジャー', ['라저']), ('了解', ['알았다', '알겠습니다', '라저', '알았어', '확인']),
]


def main():
    src = {r['key']: r for r in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))}
    ko = {}
    chunk_of = {}
    od = os.path.join(ROOT, 'work', 'translation', 'out')
    for f in os.listdir(od):
        if f.endswith('.json') and not f.endswith('.notes.json'):
            for k, v in json.load(open(os.path.join(od, f), encoding='utf-8')).items():
                ko[k] = v
                chunk_of[k] = f[:-5]
    out = []
    for jp, cands in TERMS:
        cnt = collections.defaultdict(collections.Counter)
        none = collections.Counter()
        for k, v in ko.items():
            if jp in src[k]['jp']:
                hit = [c for c in cands if c in v]
                if hit:
                    cnt[max(hit, key=len)][chunk_of[k][0]] += 1
                else:
                    none[chunk_of[k][0]] += 1
        if len(cnt) > 1 or (cnt and none):
            out.append('%s: %s | 후보 없음 %s' % (jp, {c: dict(d) for c, d in cnt.items()}, dict(none)))
    # 장 제목 vs 수집품 장소
    out.append('=== 장 제목(Settings|Title) vs 수집품 장소(Locations)')
    titles = {}
    for k, r in src.items():
        if r['file'].startswith('DT_Chapter_') and r['section'] == 'Settings' and r['name'] == 'Title' and k in ko:
            titles[r['jp']] = ko[k]
    for k, r in src.items():
        if r['file'] == 'DT_CollectItems' and r['section'] == 'Locations' and k in ko:
            m = re.match(r'ミッション\s*(\d+)\s*-\s*(.+)', r['jp'])
            if m and m.group(2).strip() in titles:
                t = titles[m.group(2).strip()]
                if t not in ko[k]:
                    out.append('%s: 장 제목 「%s」 / 수집품 「%s」' % (m.group(2), t, ko[k]))
    for jp, t in titles.items():
        out.append('  장 제목 %s → %s' % (jp, t))
    open(os.path.join(ROOT, 'work', 'survey', 'term_variants.txt'), 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
