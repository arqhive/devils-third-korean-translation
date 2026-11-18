"""2단계 출력 시험 빌드.

넣는 것
  1) Coalesced_JPN.bin: work/test_strings.json 문구로 바꿈
  2) UI_Fonts.xxx: fonts_en(GFx) 의 '国'이 있는 글꼴마다 시험 문구 한글 글리프 추가
  3) VGSBase_LOC_JPN.xxx: 자막 폰트 SubtitleFont 의 안 쓰는 한자 칸을 한글로 덮어씀
  4) WiiUTOC*.txt: 바뀐 파일 크기 반영
출력: work/build/test/sdcafiine/0005000010138F00/DevilsThirdKR/content/DevilsThirdGame/…
      work/build/test/preview_*.png (확인용)

사용: python -I tools/build_test.py [--no-toc]
"""
import json
import os
import re
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import coalesced  # noqa: E402
import gfxfont  # noqa: E402
import hangul_gfx  # noqa: E402
import subfont  # noqa: E402
import swf_tags  # noqa: E402
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402

ROOT = os.path.dirname(HERE)
GAME = os.path.join(ROOT, 'Devils Third [Game] [0005000010138f00]', 'content')
COOKED = os.path.join(GAME, 'DevilsThirdGame', 'CookedWiiU')
OUT = os.path.join(ROOT, 'work', 'build', 'test')
SD = os.path.join(OUT, 'sdcafiine', '0005000010138F00', 'DevilsThirdKR', 'content')
TTF = os.path.join(HERE, 'fonts', 'NanumGothic-Bold.ttf')


def log(*a):
    with open(os.path.join(OUT, 'build_log.txt'), 'a', encoding='utf-8') as f:
        f.write(' '.join(str(x) for x in a) + '\n')


def write(rel, data):
    p = os.path.join(SD, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(data)
    log('write', rel, len(data))


def build_coalesced(tests):
    data = open(os.path.join(COOKED, 'Coalesced_JPN.bin'), 'rb').read()
    files, _ = coalesced.parse(coalesced.decrypt(data))
    hit = set()
    for name, secs in files:
        fname = name['s'].split('\\')[-1]
        for sname, keys in secs:
            for k, v in keys:
                key = '%s|%s|%s' % (fname, sname['s'], k['s'])
                if key in tests:
                    v['s'] = tests[key]
                    v['w'] = True
                    v.pop('z', None)
                    hit.add(key)
    miss = set(tests) - hit
    if miss:
        raise SystemExit('못 찾은 키: %s' % sorted(miss))
    return coalesced.encrypt(coalesced.serialize(files)), files


def used_chars(files):
    s = set()
    for name, secs in files:
        if 'Localization' not in name['s']:
            continue
        for _, keys in secs:
            for _, v in keys:
                s |= set(v['s'])
    return s


def build_ui_fonts(chars):
    raw = open(os.path.join(COOKED, 'UI_Fonts.xxx'), 'rb').read()
    pk, body, names, imps, exps = ue3pkg.tables(raw)
    k = [i for i, e in enumerate(exps) if e['class'] == 'SwfMovie'][0]
    e = exps[k]
    exp = body[e['offset']:e['offset'] + e['size']]
    g = ue3pkg.get_array_prop(exp, names, 'RawData')
    src = hangul_gfx.HangulSource(TTF)
    rep = {}
    previews = []
    for code, p, ln in swf_tags.tags(g):
        if code != 75:
            continue
        f = gfxfont.Font3(g[p:p + ln])
        n = hangul_gfx.add_to_font(f, src, chars)
        log('gfx font', f.id, f.name.rstrip(b'\0').decode('utf-8', 'replace'), 'added', n, 'glyphs', len(f.codes))
        if n:
            rep[p] = f.serialize()
            previews.append(f)
    g2 = swf_tags.rebuild(g, rep)
    exp2 = ue3pkg.set_array_prop(exp, names, 'RawData', g2)
    return ue3pkg.repack(raw, {k: exp2}), previews


def render_gfx_preview(fonts, text, path):
    """글꼴마다 한 줄씩: 원본 일본어 '国あ' + 시험 한글."""
    rows = []
    for f in fonts:
        sc = 48 / 20480
        line = '国あ' + text
        W = int(sum((f.layout['adv'][f.codes.index(ord(c))] if ord(c) in f.codes else 10240) for c in line) * sc) + 20
        im = Image.new('L', (W, 64), 0)
        x = 10
        for c in line:
            if ord(c) not in f.codes:
                x += 10240 * sc
                continue
            i = f.codes.index(ord(c))
            cont, _ = gfxfont.decode_shape(f.shapes[i])
            acc = np.zeros((64, W), np.int32)
            for ct in cont:
                pts = []
                px, py = None, None
                for s in ct:
                    if s[0] in ('M', 'L'):
                        pts.append((s[1], s[2]))
                    else:
                        x0, y0 = pts[-1]
                        for t in np.linspace(0, 1, 6)[1:]:
                            qx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * s[1] + t * t * s[3]
                            qy = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * s[2] + t * t * s[4]
                            pts.append((qx, qy))
                m = Image.new('L', (W, 64), 0)
                ImageDraw.Draw(m).polygon([(x + px_ * sc, 50 + py_ * sc) for px_, py_ in pts], fill=1)
                sign = 1 if gfxfont.signed_area(ct) > 0 else -1
                acc += sign * np.asarray(m, np.int32)
            im = Image.fromarray(np.maximum(np.asarray(im), (acc > 0).astype(np.uint8) * 255))
            x += f.layout['adv'][i] * sc
        rows.append(im)
    W = max(r.width for r in rows)
    sheet = Image.new('L', (W, 64 * len(rows)), 0)
    for i, r in enumerate(rows):
        sheet.paste(r, (0, 64 * i))
    sheet.save(path)


def build_vgsbase(chars, keep):
    raw = open(os.path.join(COOKED, 'VGSBase_LOC_JPN.xxx'), 'rb').read()
    inner = bytearray(ue3full.unpack(raw))
    pk, body, names, imps, exps = ue3pkg.tables(bytes(inner))
    assert not pk.chunks
    fe = [e for e in exps if e['name'] == 'SubtitleFont'][0]
    font_exp = bytes(inner[fe['offset']:fe['offset'] + fe['size']])
    import ue3font
    _, props, _ = ue3font.parse_font(font_exp, names)
    tex = [p for p in props if p.name == 'Textures'][0].raw
    n = struct.unpack('>i', tex[:4])[0]
    refs = struct.unpack('>%di' % n, tex[4:])
    pe = [exps[r - 1] for r in refs]
    page_exps = [bytes(inner[e['offset']:e['offset'] + e['size']]) for e in pe]
    sizes = [(512, 1024) if e['size'] > 500000 else ((512, 256) if e['size'] < 200000 else (512, 512)) for e in pe]
    new_font, new_pages, report, imgs = subfont.inject(font_exp, names, page_exps, sizes, chars, TTF, keep=keep)
    assert len(new_font) == len(font_exp)
    inner[fe['offset']:fe['offset'] + fe['size']] = new_font
    for e, b in zip(pe, new_pages):
        assert len(b) == e['size']
        inner[e['offset']:e['offset'] + e['size']] = b
    for r in report:
        log('subtitle', *r)
    # 미리보기: 바꾼 칸들을 확대해 한 장으로
    tiles = []
    for ch, old, ti, su, sv, us, vs, top in report:
        a = imgs[ti][sv:sv + vs, su:su + us, 3]
        t = Image.new('L', (32, 40), 40)
        t.paste(Image.fromarray(a), (2, 2 + max(0, top - 8)))
        tiles.append(t.resize((96, 120), Image.NEAREST))
    if tiles:
        cols = 16
        sheet = Image.new('L', (96 * cols, 120 * ((len(tiles) + cols - 1) // cols)), 0)
        for i, t in enumerate(tiles):
            sheet.paste(t, (96 * (i % cols), 120 * (i // cols)))
        sheet.save(os.path.join(OUT, 'preview_subtitle_cells.png'))
    return ue3full.pack(bytes(inner), 6), len(inner)


def update_toc(sizes):
    base = os.path.join(GAME, 'DevilsThirdGame')
    for toc in ('WiiUTOC.txt', 'WiiUTOC_JPN.txt', 'WiiUTOC_FRA.txt'):
        lines = open(os.path.join(base, toc), 'rb').read().split(b'\r\n')
        changed = 0
        for i, ln in enumerate(lines):
            m = re.match(rb'^(\d+) (\d+) (\S+) (\d+)$', ln)
            if not m:
                continue
            path = m.group(3).decode('ascii')
            for rel, (size, usize) in sizes.items():
                if path.lower() == ('..\\DevilsThirdGame\\' + rel.replace('/', '\\')).lower():
                    u = m.group(2) if usize is None else str(usize).encode()
                    lines[i] = b'%d %s %s %s' % (size, u, m.group(3), m.group(4))
                    changed += 1
        write('DevilsThirdGame/' + toc, b'\r\n'.join(lines))
        log('toc', toc, 'changed', changed)


def main():
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'build_log.txt'), 'w').close()
    tests = {k: v for k, v in json.load(open(os.path.join(ROOT, 'work', 'test_strings.json'), encoding='utf-8')).items()
             if not k.startswith('_')}
    chars = sorted({c for v in tests.values() for c in v if 0xAC00 <= ord(c) <= 0xD7A3})
    log('hangul chars', len(chars), ''.join(chars))

    coal, files = build_coalesced(tests)
    write('DevilsThirdGame/CookedWiiU/Coalesced_JPN.bin', coal)
    keep = used_chars(files)

    ui, fonts = build_ui_fonts(chars)
    write('DevilsThirdGame/CookedWiiU/UI_Fonts.xxx', ui)
    render_gfx_preview(fonts, '솔로 플레이 수용소에서 탈출하라', os.path.join(OUT, 'preview_gfx_fonts.png'))

    vgs, vgs_usize = build_vgsbase(chars, keep)
    write('DevilsThirdGame/CookedWiiU/VGSBase_LOC_JPN.xxx', vgs)

    sizes = {'CookedWiiU/Coalesced_JPN.bin': (len(coal), None),
             'CookedWiiU/UI_Fonts.xxx': (len(ui), None),
             'CookedWiiU/VGSBase_LOC_JPN.xxx': (len(vgs), vgs_usize)}
    if '--no-toc' not in sys.argv:
        update_toc(sizes)
    log('done')


if __name__ == '__main__':
    main()
