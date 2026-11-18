"""번역 넘침 검사.

입력 JSON: {"파일|구역|키": "번역문", ...}  (파일은 확장자 없이 또는 .JPN 붙여도 됨, '_'로 시작하는 키는 무시)
UI 글: 줄마다 폭(em, OptiB 기준, 한글 1자 = '国' 폭 0.85em) ≤ 세 언어 최대 폭, 줄 수 ≤ 세 언어 최대 줄 수
자막: 줄마다 폭(px, 자막 폰트) ≤ 한도(기본 = 일본어 자막 최대 688px, --sub-limit 로 바꿈), 줄 수 ≤ 그 키 세 언어 최대 줄 수
  한글 자막 폭은 실제로 넣을 방식(잉크 너비 + 간격 2px, 기준 '国' 높이)으로 TTF 를 그려 잰다(--ttf).

사용: python -I tools/check_overflow.py <번역.json> [--ttf tools/fonts/NanumGothic-Bold.ttf] [--sub-limit 688] [--ratio 1.0]
출력: 넘친 줄 목록(work/survey/overflow_report.txt), 종료 코드 = 넘친 수(최대 255)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure  # noqa: E402
import subfont  # noqa: E402

ROOT = os.path.dirname(HERE)


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def norm_key(k):
    fn, sec, key = k.split('|')
    return '%s|%s|%s' % (re.sub(r'\.(JPN|jpn)$', '', fn), sec, key)


def main():
    src = sys.argv[1]
    ttf = arg('--ttf', os.path.join(HERE, 'fonts', 'NanumGothic-Bold.ttf'))
    sub_limit = int(arg('--sub-limit', 688))
    ratio = float(arg('--ratio', 1.0))
    lim = json.load(open(os.path.join(ROOT, 'work', 'survey', 'limits.json'), encoding='utf-8'))
    keys = lim['keys']
    gf = measure.gfx_font()
    ui = measure.Width(gf, gf[ord('国')], gf[ord('国')])
    sj = measure.sub_font(os.path.join(measure.COOKED, 'VGSBase_LOC_JPN.xxx'), True)
    rnd = subfont.Renderer(ttf, 21, 10)
    cache = {}

    def hw(c):
        if c not in cache:
            crop, _ = rnd.glyph(c)
            cache[c] = crop.shape[1] + rnd.gap
        return cache[c]
    sub = measure.Width(sj, hw, sj[ord('国')])

    tr = {norm_key(k): v for k, v in json.load(open(src, encoding='utf-8')).items() if not k.startswith('_')}
    bad = []
    unknown = []
    for k, text in tr.items():
        if k not in keys:
            unknown.append(k)
            continue
        L = keys[k]
        if L['kind'] == 'ui':
            ws = [w / 20480 for w in ui.lines(text)]
            if len(ws) > L['lines']:
                bad.append((k, 'lines %d > %d' % (len(ws), L['lines']), text))
            for i, w in enumerate(ws):
                if w > L['w_em'] * ratio + 0.001:
                    bad.append((k, 'line %d: %.2fem > %.2fem' % (i + 1, w, L['w_em'] * ratio), text))
        else:
            ws = sub.lines(text)
            if len(ws) > L['lines']:
                bad.append((k, 'lines %d > %d' % (len(ws), L['lines']), text))
            for i, w in enumerate(ws):
                if w > sub_limit:
                    bad.append((k, 'line %d: %dpx > %dpx' % (i + 1, w, sub_limit), text))
    out = os.path.join(ROOT, 'work', 'survey', 'overflow_report.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('checked %d, overflow %d, unknown keys %d\n' % (len(tr), len(bad), len(unknown)))
        for b in bad:
            f.write('%s | %s | %s\n' % (b[0], b[1], b[2].replace('\n', '/')))
        for u in unknown:
            f.write('UNKNOWN %s\n' % u)
    print('checked', len(tr), 'overflow', len(bad), 'unknown', len(unknown))
    return min(len(bad), 255)


if __name__ == '__main__':
    sys.exit(main())
