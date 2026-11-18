"""번역 범위(solo)를 덩어리로 나눈다. 자막은 장 단위(장면이 쪼개지지 않게), 장면 순서(order)를 붙인다.
출력: work/translation/src/<덩어리>.json  (항목: key, file, section, name, group, jp, en, fr, speaker, kind, lines, limit_em, order)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS = {
    'A_ch00-02': ['DT_Chapter_00', 'DT_Chapter_01', 'DT_Chapter_02'],
    'B_ch03-04': ['DT_Chapter_03', 'DT_Chapter_03_Mg1', 'DT_Chapter_03_Mg2', 'DT_Chapter_04', 'DT_Chapter_04_Mg1',
                  'DT_Chapter_04_Mg2'],
    'C_ch05-07': ['DT_Chapter_05', 'DT_Chapter_05_Mg1', 'DT_Chapter_06', 'DT_Chapter_07', 'DT_Chapter_07_Mg1'],
    'D_ch08-09': ['DT_Chapter_08', 'DT_Chapter_08_Mg1', 'DT_Chapter_08_Mg2', 'DT_Chapter_09'],
    'F_messagebox': ['DT_UI_MessageBox'],
    'G_ui': ['DT_Game_Generic', 'DT_UI_Labels', 'DT_UI_Pause', 'DT_UI_Tutorial', 'DT_ShootingRaqnge',
             'DT_UI_Labels_Ranking', 'UnlockGore'],
    'H_weapon_tips': ['DT_Weapons', 'DT_Tips'],
}


def main():
    rows = [x for x in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
            if x['scope'] == 'solo']
    out = os.path.join(ROOT, 'work', 'translation', 'src')
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'work', 'translation', 'out'), exist_ok=True)
    for i, x in enumerate(rows):
        m = re.match(r'^L_(\d+)$', x['name'])
        x['order'] = int(m.group(1)) if m else i
    done = set()
    report = []
    for name, files in CHUNKS.items():
        sel = [x for x in rows if x['file'] in files]
        sel.sort(key=lambda x: (files.index(x['file']), x['section'], x['order']))
        json.dump(sel, open(os.path.join(out, name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        done |= {x['key'] for x in sel}
        report.append('%s\t%d줄\t%d자' % (name, len(sel), sum(len(x['jp']) for x in sel)))
    # 수집품은 두 덩어리(길이 반씩)
    col = [x for x in rows if x['file'] == 'DT_CollectItems']
    col.sort(key=lambda x: (x['name'], x['section']))
    total = sum(len(x['jp']) for x in col)
    acc = 0
    cut = 0
    for j, x in enumerate(col):
        acc += len(x['jp'])
        if acc >= total / 2:
            cut = j + 1
            break
    # 같은 이름(name)끼리는 한 덩어리에
    while cut < len(col) and col[cut]['name'] == col[cut - 1]['name']:
        cut += 1
    for name, sel in (('E1_collect', col[:cut]), ('E2_collect', col[cut:])):
        json.dump(sel, open(os.path.join(out, name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        done |= {x['key'] for x in sel}
        report.append('%s\t%d줄\t%d자' % (name, len(sel), sum(len(x['jp']) for x in sel)))
    left = [x['key'] for x in rows if x['key'] not in done]
    report.append('남은 줄 %d %s' % (len(left), left[:5]))
    print('\n'.join(report))


if __name__ == '__main__':
    main()
