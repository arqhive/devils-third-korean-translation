"""게임이 쓰는 글꼴 견본 시트(원본 글리프를 그대로 그림).

- GFx(fonts_en) DefineFont3 11개: 벡터 도형을 4배로 그린 뒤 줄여 매끈하게
- UE3 비트맵: 자막 SubtitleFont·SkipFont(VGSBase_LOC_JPN), 영어판 SubtitleFont(UI_Fonts)
- 무비 내장 MS PMincho(DsrExchange)
출력: work/survey/font_specimen.png
"""
import json
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gfxfont  # noqa: E402
import swf_tags  # noqa: E402
import ue3font  # noqa: E402
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402
import ue3tex  # noqa: E402

ROOT = os.path.dirname(HERE)
COOKED = os.path.join(ROOT, 'Devils Third [Game] [0005000010138f00]', 'content', 'DevilsThirdGame', 'CookedWiiU')
JP = 'ソロプレイ 収容所から脱出せよ どうかしたのかね アイヴァン'
EN = 'DEVIL\'S THIRD  Mission 1  0123456789'
LABEL_FONT = 'C:/Windows/Fonts/malgunbd.ttf'

USE = {
    'Mechanical-NewRodinUB': '$SpecialFont_en / SpecialFont2 — 솔로 글상자 581개(제목·버튼·큰 글씨)',
    'OptiB-NewRodinB85-NTLGDB002': '$NormalFont / _en / _jp — 솔로 글상자 543개(메뉴·설명 기본)',
    'Journal': '$NumberFont_en — 솔로 글상자 145개(숫자, 일본어 없음)',
    'Eurostile Next LT Pro': '$NumberFont(공통) — 숫자·영문',
    'NewCezProBNTLGD002_3': '논리 이름 연결 없음(이름 직접 지정 칸만)',
    'Mechanical-NewRodinUB-NT002': '논리 이름 연결 없음(이름 직접 지정 칸만)',
    'FTT-Utrillo DB': '견본용 소형 글꼴(92자)',
    'MS UI Gothic': '견본용 소형 글꼴(122자)',
    'FTT-ニューセザンヌ B': '견본용 소형 글꼴(30자)',
    'FTT-セザンヌ墨東 B': '견본용 소형 글꼴(92자)',
    'FTT-豊隷 EB': '견본용 소형 글꼴(122자)',
}


def render_vec(f, text, px=44, ss=4):
    sc = px * ss / 20480
    asc = (f.layout['asc'] if f.layout else 20480) * sc
    H = int(px * ss * 1.45)
    idx = {c: i for i, c in enumerate(f.codes)}
    W = int(sum((f.layout['adv'][idx[ord(c)]] if ord(c) in idx else 10240) for c in text) * sc) + 8 * ss
    acc = np.zeros((H, W), np.int32)
    x = 4 * ss
    base = asc + 4 * ss
    for c in text:
        i = idx.get(ord(c))
        if i is None:
            x += 10240 * sc
            continue
        cont, _ = gfxfont.decode_shape(f.shapes[i])
        for ct in cont:
            pts = []
            for s in ct:
                if s[0] in ('M', 'L'):
                    pts.append((s[1], s[2]))
                else:
                    x0, y0 = pts[-1]
                    for t in np.linspace(0, 1, 8)[1:]:
                        pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * s[1] + t * t * s[3],
                                    (1 - t) ** 2 * y0 + 2 * (1 - t) * t * s[2] + t * t * s[4]))
            if len(pts) < 3:
                continue
            m = Image.new('L', (W, H), 0)
            ImageDraw.Draw(m).polygon([(x + a * sc, base + b * sc) for a, b in pts], fill=1)
            acc += (1 if gfxfont.signed_area(ct) > 0 else -1) * np.asarray(m, np.int32)
        x += (f.layout['adv'][i] if f.layout else 20480) * sc
    im = Image.fromarray(((acc > 0) * 255).astype(np.uint8))
    return im.resize((W // ss, H // ss), Image.LANCZOS)


def ue3_bitmap(path, full, name):
    raw = open(path, 'rb').read()
    if full:
        raw = ue3full.unpack(raw)
    pk, body, names, imps, exps = ue3pkg.tables(raw)
    e = [e for e in exps if e['name'] == name][0]
    net, props, native = ue3font.parse_font(body[e['offset']:e['offset'] + e['size']], names)
    chars = ue3font.chars_of([p for p in props if p.name == 'Characters'][0].raw)
    pairs, _ = ue3font.remap_of(native)
    tex = [p for p in props if p.name == 'Textures'][0].raw
    n = struct.unpack('>i', tex[:4])[0]
    refs = struct.unpack('>%di' % n, tex[4:])
    pages = []
    for r in refs:
        ex = exps[r - 1]
        b = body[ex['offset']:ex['offset'] + ex['size']]
        h = 1024 if ex['size'] > 500000 else (512 if ex['size'] > 200000 else (256 if ex['size'] > 100000 else 128))
        w = 512 if ex['size'] > 100000 else 128
        try:
            pages.append(ue3tex.decode_page(b, w, h)[0])
        except Exception:  # noqa: BLE001
            pages.append(None)
    return chars, dict(pairs), pages, len(pairs)


def render_bitmap(chars, remap, pages, text, scale=1.6):
    line_h = max(c[3] + c[5] for c in chars) + 4
    W = sum(chars[remap[ord(c)]][2] if ord(c) in remap else 12 for c in text) + 8
    im = np.zeros((line_h, W), np.uint8)
    x = 4
    for c in text:
        if ord(c) not in remap:
            x += 12
            continue
        su, sv, us, vs, ti, vo = chars[remap[ord(c)]]
        pg = pages[ti]
        if pg is not None and vs > 0 and us > 0:
            a = pg[sv:sv + vs, su:su + us, 3]
            im[vo:vo + a.shape[0], x:x + a.shape[1]] = np.maximum(im[vo:vo + a.shape[0], x:x + a.shape[1]], a)
        x += us
    out = Image.fromarray(im)
    return out.resize((int(W * scale), int(line_h * scale)), Image.LANCZOS)


def main():
    lab = ImageFont.truetype(LABEL_FONT, 20)
    small = ImageFont.truetype(LABEL_FONT, 15)
    rows = []
    raw = open(os.path.join(COOKED, 'UI_Fonts.xxx'), 'rb').read()
    pk, body, names, imps, exps = ue3pkg.tables(raw)
    e = [e for e in exps if e['class'] == 'SwfMovie'][0]
    g = ue3pkg.get_array_prop(body[e['offset']:e['offset'] + e['size']], names, 'RawData')
    n = 0
    for code, p, ln in swf_tags.tags(g):
        if code != 75:
            continue
        n += 1
        f = gfxfont.Font3(g[p:p + ln])
        nm = f.name.rstrip(b'\0').decode('utf-8', 'replace')
        kana = sum(1 for c in f.codes if 0x3040 <= c <= 0x30ff)
        kanji = sum(1 for c in f.codes if 0x4e00 <= c <= 0x9fff)
        title = 'G%d. %s  [메뉴 벡터 글꼴 · %d자: 가나 %d, 한자 %d]' % (n, nm, len(f.codes), kana, kanji)
        rows.append((title, USE.get(nm, ''), [render_vec(f, JP), render_vec(f, EN)]))
    # UE3 비트맵
    for label, path, full, name, use in [
        ('자막 SubtitleFont (일본어판)', 'VGSBase_LOC_JPN.xxx', True, 'SubtitleFont',
         '컷신·게임 중 자막(원본 글꼴 이름 FOT-ニューセザンヌ Pro B, 비트맵 DXT5)'),
        ('자막 SubtitleFont (영어·프랑스어판)', 'UI_Fonts.xxx', False, 'SubtitleFont', '참고: 영어판 자막'),
        ('건너뛰기 SkipFont', 'VGSBase_LOC_JPN.xxx', True, 'SkipFont', '컷신 건너뛰기 안내(13자)'),
    ]:
        chars, remap, pages, cnt = ue3_bitmap(os.path.join(COOKED, path), full, name)
        imgs = [render_bitmap(chars, remap, pages, JP), render_bitmap(chars, remap, pages, EN)]
        if name == 'SkipFont':
            imgs = [render_bitmap(chars, remap, pages, ''.join(chr(k) for k in sorted(remap)))]
        rows.append(('B. %s  [UE3 비트맵 · %d자]' % (label, cnt), use, imgs))
    # 시트
    W = max(max(i.width for i in r[2]) for r in rows) + 40
    H = sum(60 + sum(i.height + 6 for i in r[2]) for r in rows) + 20
    sheet = Image.new('RGB', (max(W, 900), H), (22, 24, 30))
    d = ImageDraw.Draw(sheet)
    y = 10
    for title, use, imgs in rows:
        d.text((16, y), title, font=lab, fill=(255, 210, 90))
        d.text((16, y + 28), use, font=small, fill=(170, 200, 255))
        y += 56
        for im in imgs:
            sheet.paste(Image.merge('RGB', [im, im, im]), (24, y))
            y += im.height + 6
        d.line([(10, y + 2), (sheet.width - 10, y + 2)], fill=(70, 70, 80))
        y += 8
    out = os.path.join(ROOT, 'work', 'survey', 'font_specimen.png')
    sheet.save(out)
    print(out, sheet.size)


if __name__ == '__main__':
    main()
