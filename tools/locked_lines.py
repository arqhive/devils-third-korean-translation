"""사용자가 직접 정한 줄 목록(재검수 때 건드리지 않음) → work/review2/locked.json {key: 이유}

출처
- apply_notes.py 의 SET·REPLACE 키(5단계 질문거리 결정)
- よろしいですか → 「괜찮습니까?」 통일(사용자 결정)
- 7단계 사용자 결정: おいおい 4줄(검수 안 선택), 有効 5줄(「효과적」 유지)
- 그 뒤 사용자가 문구를 직접 지정한 줄(옹이구멍, GamePad를 봐 주세요 등)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import apply_notes  # noqa: E402

locked = {}
for k in apply_notes.SET:
    locked[k] = '5단계 질문거리 사용자 결정(문구 지정)'
for k, _, _ in apply_notes.REPLACE:
    locked[k] = '5단계 질문거리 사용자 결정(낱말 지정, 그 낱말만 고정)'
src = json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
for r in src:
    if r['scope'] == 'solo' and 'よろしいですか' in r['jp']:
        locked.setdefault(r['key'], '「よろしいですか → 괜찮습니까?」 통일(사용자 결정, 그 부분만 고정)')
for k in ['DT_Chapter_02|Subs_R180|L_014', 'DT_Chapter_03|Subs_R140|L_014', 'DT_Chapter_04|Subs_R140|L_001',
          'DT_Chapter_07_Mg1|Subs_Set01|L_004']:
    locked[k] = '7단계 おいおい 줄(사용자가 검수 안 선택)'
for k in ['DT_Tips|Multi_Single|Action_22', 'DT_Tips|Single|Enemy_01', 'DT_Tips|Single|Enemy_02',
          'DT_Tips|Single|Enemy_06', 'DT_Tips|Single|Enemy_08']:
    locked[k] = '7단계 有効 → 「효과적」 유지(사용자 결정)'
locked['DT_UI_Labels|Notice|WatchDRC'] = '사용자 문구 지정(GamePad를 봐 주세요.)'
locked['DT_UI_Labels|Notice|ChangeTV_URCC'] = '사용자 확인(마침표 추가)'
locked['DT_CollectItems|Descriptions|EB_08'] = '7단계 「데브그루의 존재」 사용자 승인(그 부분만 고정)'
out = os.path.join(ROOT, 'work', 'review2')
os.makedirs(out, exist_ok=True)
json.dump(locked, open(os.path.join(out, 'locked.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('고정 줄', len(locked))
