"""원본 글꼴과 한글 후보(TTF 굵기별)를 실제 주입 방식 그대로 그려 비교한다.

메뉴 벡터 글꼴: hangul_gfx 로 '国' 상자에 맞춘 한글 글리프를 원본 글꼴 사본에 넣고 font_specimen.render_vec 로 그림
                (영문·숫자는 원본 글리프 그대로 → 섞였을 때 어울림 확인)
자막 비트맵: subfont.Renderer(실제 크기 '国' 21px)로 그린 한글 칸을 원본 자막 줄 옆에 놓음
사용: python -I tools/font_compare.py <TTF 접두어(예: tools/fonts/SB_Aggro_)> <굵기 목록 예: L,M,B> <출력.png>
"""
import copy
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import font_specimen as fs  # noqa: E402
import gfxfont  # noqa: E402
import hangul_gfx  # noqa: E402
import subfont  # noqa: E402
import swf_tags  # noqa: E402
import ue3pkg  # noqa: E402

JP = 'ソロプレイ 収容所から脱出せよ'
KO = '솔로 플레이  수용소에서 탈출하라'
MIX = 'Mission 1 - 뒷마당의 무법자  0123'
SUB_JP = 'どうかしたのかね アイヴァン'
SUB_KO = '무슨 일인가, 아이반.'
SUB_KO2 = '교도소 전원이 비상용으로 바뀌는 바람에'


def gfx_fonts():
    raw = open(os.path.join(fs.COOKED, 'UI_Fonts.xxx'), 'rb').read()
    pk, body, names, imps, exps = ue3pkg.tables(raw)
    e = [e for e in exps if e['class'] == 'SwfMovie'][0]
    g = ue3pkg.get_array_prop(body[e['offset']:e['offset'] + e['size']], names, 'RawData')
    out = {}
    for code, p, ln in swf_tags.tags(g):
        if code == 75:
            f = gfxfont.Font3(g[p:p + ln])
            out[f.name.rstrip(b'\0').decode('utf-8', 'replace')] = f
    return out


def bitmap_line(rnd, text, scale=1.6):
    """자막 한 줄: 한글은 Renderer 칸, 공백 7px, 문장부호는 같은 TTF 로 그림(시험용)."""
    cells = []
    for c in text:
        if c == ' ':
            cells.append((None, 7, 0))
            continue
        crop, top = rnd.glyph(c)
        cells.append((crop, crop.shape[1] + rnd.gap, top))
    H = 40
    W = sum(w for _, w, _ in cells) + 8
    im = np.zeros((H, W), np.uint8)
    x = 4
    for crop, w, top in cells:
        if crop is not None:
            h = min(crop.shape[0], H - max(top, 0))
            im[max(top, 0):max(top, 0) + h, x:x + crop.shape[1]] = crop[:h]
        x += w
    out = Image.fromarray(im)
    return out.resize((int(W * scale), int(H * scale)), Image.LANCZOS)


def main():
    prefix, weights, out = sys.argv[1], sys.argv[2].split(','), sys.argv[3]
    lab = ImageFont.truetype(fs.LABEL_FONT, 20)
    small = ImageFont.truetype(fs.LABEL_FONT, 15)
    fonts = gfx_fonts()
    blocks = []
    for fname, role in [('Mechanical-NewRodinUB', '① 굵은 제목체 $SpecialFont (원본 울트라 볼드)'),
                        ('OptiB-NewRodinB85-NTLGDB002', '② 기본 고딕 $NormalFont (원본 볼드)'),
                        ('NewCezProBNTLGD002_3', 'G4 NewCezPro (이름 직접 지정 칸)')]:
        base = fonts[fname]
        rows = [('원본 일본어', fs.render_vec(base, JP))]
        for w in weights:
            f = copy.deepcopy(base)
            src = hangul_gfx.HangulSource(prefix + w + '.ttf')
            hangul_gfx.add_to_font(f, src, sorted(set(c for c in KO + MIX if 0xAC00 <= ord(c) <= 0xD7A3)))
            rows.append(('어그로 %s' % w, fs.render_vec(f, KO)))
            rows.append(('어그로 %s + 원본 영문' % w, fs.render_vec(f, MIX)))
        blocks.append((role, fname, rows))
    # 자막
    chars, remap, pages, cnt = fs.ue3_bitmap(os.path.join(fs.COOKED, 'VGSBase_LOC_JPN.xxx'), True, 'SubtitleFont')
    rows = [('원본 일본어(실제 크기 ×1.6)', fs.render_bitmap(chars, remap, pages, SUB_JP))]
    for w in weights:
        rnd = subfont.Renderer(prefix + w + '.ttf', 21, 10)
        rows.append(('어그로 %s' % w, bitmap_line(rnd, SUB_KO)))
        rows.append(('어그로 %s' % w, bitmap_line(rnd, SUB_KO2)))
    blocks.append(('③ 자막체 SubtitleFont (원본 ニューセザンヌ B, 비트맵)', 'VGSBase_LOC_JPN', rows))

    W = 1100
    H = sum(60 + sum(r[1].height + 10 for r in b[2]) for b in blocks) + 20
    sheet = Image.new('RGB', (W, H), (22, 24, 30))
    d = ImageDraw.Draw(sheet)
    y = 10
    for role, fname, rows in blocks:
        d.text((16, y), role, font=lab, fill=(255, 210, 90))
        d.text((16, y + 28), fname, font=small, fill=(170, 200, 255))
        y += 56
        for label, im in rows:
            d.text((16, y + im.height // 2 - 9), label, font=small, fill=(200, 200, 200))
            sheet.paste(Image.merge('RGB', [im, im, im]), (230, y))
            y += im.height + 10
        d.line([(10, y), (W - 10, y)], fill=(70, 70, 80))
        y += 8
    sheet.save(out)
    print(out, sheet.size)


if __name__ == '__main__':
    main()
