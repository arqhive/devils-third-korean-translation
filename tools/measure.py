"""3단계 창 측정: 키마다 폭 한도 만들기.

UI 글(자막 아닌 것): GFx 글꼴(기본 OptiB-NewRodinB85 = $NormalFont) 진행 폭 합(em, 20480=1em)으로 잰다.
  한도 = 같은 키의 JPN·INT·FRA 줄 폭 최댓값(같은 글상자에 세 언어가 다 들어가므로), 줄 수 한도 = 세 언어 최대 줄 수.
자막(DT_Chapter_* 의 Subs_* 구역 L_### 값): UE3 SubtitleFont 칸 폭(USize) 합(px).
  JPN 은 VGSBase_LOC_JPN 의 폰트, INT·FRA 는 UI_Fonts 의 폰트로 잰다. 한도 = 세 언어 전체 자막 줄 폭 최댓값(화면 폭 기준).
출력: work/survey/limits.json, work/survey/window_table.md
"""
import collections
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gfxfont  # noqa: E402
import swf_tags  # noqa: E402
import ue3font  # noqa: E402
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402

ROOT = os.path.dirname(HERE)
COOKED = os.path.join(ROOT, 'Devils Third [Game] [0005000010138f00]', 'content', 'DevilsThirdGame', 'CookedWiiU')
S = os.path.join(ROOT, 'work', 'survey')
SUB_SEC = re.compile(r'^Subs_')
SUB_KEY = re.compile(r'^L_\d+$')
TAG = re.compile(r'<[^>]+>')


def load_coal(lang):
    f = json.load(open(os.path.join(ROOT, 'work', 'extract', 'coalesced', lang + '.json'), encoding='utf-8'))
    out = {}
    for n, s in f:
        if 'Localization' not in n['s']:
            continue
        fn = n['s'].split('\\')[-1].rsplit('.', 1)[0]
        for sn, ks in s:
            for k, v in ks:
                out['%s|%s|%s' % (fn, sn['s'], k['s'])] = v['s']
    return out


def gfx_font(name_prefix=b'OptiB'):
    raw = open(os.path.join(COOKED, 'UI_Fonts.xxx'), 'rb').read()
    pk, body, names, imps, exps = ue3pkg.tables(raw)
    e = [e for e in exps if e['class'] == 'SwfMovie'][0]
    g = ue3pkg.get_array_prop(body[e['offset']:e['offset'] + e['size']], names, 'RawData')
    for code, p, ln in swf_tags.tags(g):
        if code == 75:
            f = gfxfont.Font3(g[p:p + ln])
            if f.name.startswith(name_prefix):
                return dict(zip(f.codes, f.layout['adv']))


def sub_font(path, full):
    raw = open(path, 'rb').read()
    if full:
        raw = ue3full.unpack(raw)
    pk, body, names, imps, exps = ue3pkg.tables(raw)
    e = [e for e in exps if e['name'] == 'SubtitleFont'][0]
    net, props, native = ue3font.parse_font(body[e['offset']:e['offset'] + e['size']], names)
    chars = ue3font.chars_of([p for p in props if p.name == 'Characters'][0].raw)
    pairs, _ = ue3font.remap_of(native)
    return {k: chars[v][2] for k, v in pairs}


class Width:
    def __init__(self, table, hangul, default):
        self.t, self.h, self.d = table, hangul, default

    def char(self, c):
        o = ord(c)
        if 0xAC00 <= o <= 0xD7A3:
            return self.h(c) if callable(self.h) else self.h
        return self.t.get(o, self.d)

    def line(self, s):
        return sum(self.char(c) for c in s)

    def lines(self, text):
        return [self.line(x) for x in TAG.sub('', text).replace('\r', '').split('\n')]


def is_sub(key):
    fn, sec, k = key.split('|')
    return fn.startswith('DT_Chapter_') and SUB_SEC.match(sec) and SUB_KEY.match(k)


def build():
    vals = {L: load_coal(L) for L in ('JPN', 'INT', 'FRA')}
    gf = gfx_font()
    em = 20480
    ui_w = Width(gf, gf[ord('国')], gf[ord('国')])
    sj = sub_font(os.path.join(COOKED, 'VGSBase_LOC_JPN.xxx'), True)
    si = sub_font(os.path.join(COOKED, 'UI_Fonts.xxx'), False)
    sub_w = {'JPN': Width(sj, sj[ord('国')], sj[ord('国')]), 'INT': Width(si, si.get(ord('M'), 20), 20),
             'FRA': Width(si, si.get(ord('M'), 20), 20)}
    limits = {}
    sub_max = collections.Counter()
    sub_lines = collections.Counter()
    for key, jtext in vals['JPN'].items():
        if not re.search('[぀-ヿ一-鿿]', jtext):
            continue
        if is_sub(key):
            per = {}
            for L in ('JPN', 'INT', 'FRA'):
                t = vals[L].get(key)
                if t is None:
                    continue
                ws = sub_w[L].lines(t)
                sub_max[L] = max(sub_max[L], max(ws))
                sub_lines[L] = max(sub_lines[L], len(ws))
                per[L] = {'px': max(ws), 'lines': len(ws)}
            limits[key] = {'kind': 'subtitle', 'lines': max(p['lines'] for p in per.values()), 'by_lang': per}
        else:
            per = {}
            for L in ('JPN', 'INT', 'FRA'):
                t = vals[L].get(key)
                if t is None:
                    continue
                ws = ui_w.lines(t)
                per[L] = {'w': round(max(ws) / em, 3), 'lines': len(ws)}
            limits[key] = {'kind': 'ui', 'w_em': max(p['w'] for p in per.values()),
                           'lines': max(p['lines'] for p in per.values()), 'by_lang': per}
    sub_limit = max(sub_max.values())
    meta = {'subtitle_px': sub_limit, 'subtitle_by_lang': dict(sub_max), 'subtitle_lines': dict(sub_lines),
            'ui_font': 'OptiB-NewRodinB85-NTLGDB002', 'hangul_em': round(gf[ord('国')] / em, 3)}
    json.dump({'meta': meta, 'keys': limits}, open(os.path.join(S, 'limits.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    return meta, limits


if __name__ == '__main__':
    meta, limits = build()
    print(json.dumps(meta, ensure_ascii=True))
    print('keys', len(limits), collections.Counter(v['kind'] for v in limits.values()))
