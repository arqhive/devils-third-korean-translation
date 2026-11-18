"""자간 안 비교 시트(굵기 확정: 제목 B, 기본 M, 자막 M).

메뉴: A 고정('国' 폭) / B 어그로 자체 폭 / C 자체 폭 -5% / D 자체 폭 -10%  (B~D 는 띄어쓰기도 어그로 폭)
자막: 잉크+2px(현재) / 잉크+1px / 어그로 자체 폭(글꼴 진행 폭 그대로)
사용: python -I tools/spacing_compare.py <출력.png>
"""
import copy
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import font_compare as fc  # noqa: E402
import font_specimen as fs  # noqa: E402
import hangul_gfx  # noqa: E402
import subfont  # noqa: E402

FONTS = os.path.join(HERE, 'fonts')
T1 = '솔로 플레이  수용소에서 탈출하라'
T2 = '리로드 중에 빈틈이 생기는 건 적만이 아니다'
T3 = 'Mission 1 - 뒷마당의 무법자  0123'
S1 = '무슨 일인가, 아이반.'
S2 = '교도소 전원이 비상용으로 바뀌는 바람에'
S3 = '자랑하는 스피커 소리가 엉망이야'


def sub_natural(ttf, text, scale=1.6):
    """어그로 자체 진행 폭으로 그린 자막 줄(크기·세로 위치는 Renderer 와 같게)."""
    rnd = subfont.Renderer(ttf, 21, 10)
    font = rnd.font
    W = int(font.getlength(text)) + 10
    im = Image.new('L', (W, 96), 0)
    ImageDraw.Draw(im).text((4, 72), text, font=font, fill=255, anchor='ls')
    a = np.asarray(im)
    top = int(rnd.line_top)
    a = a[top:top + 40]
    out = Image.fromarray(np.ascontiguousarray(a))
    return out.resize((int(out.width * scale), int(out.height * scale)), Image.LANCZOS)


def main():
    out = sys.argv[1]
    lab = ImageFont.truetype(fs.LABEL_FONT, 20)
    small = ImageFont.truetype(fs.LABEL_FONT, 15)
    fonts = fc.gfx_fonts()
    blocks = []
    variants = [('A 고정(현재)', 'fixed', 0.0, None), ('B 어그로 자체 폭', 'natural', 0.0, 'ttf'),
                ('C 자체 폭 -5%', 'natural', -0.05, 'ttf'), ('D 자체 폭 -10%', 'natural', -0.10, 'ttf')]
    chars = sorted(set(c for c in T1 + T2 + T3 if 0xAC00 <= ord(c) <= 0xD7A3))
    for fname, w, role in [('Mechanical-NewRodinUB', 'B', '① 굵은 제목체 — 어그로 B'),
                           ('OptiB-NewRodinB85-NTLGDB002', 'M', '② 기본 고딕 — 어그로 M')]:
        base = fonts[fname]
        rows = [('원본 일본어', fs.render_vec(base, fc.JP))]
        src = hangul_gfx.HangulSource(os.path.join(FONTS, 'SB_Aggro_%s.ttf' % w))
        for label, mode, track, space in variants:
            f = copy.deepcopy(base)
            hangul_gfx.add_to_font(f, src, chars, mode=mode, track=track, space=space)
            for t in (T1, T2, T3):
                rows.append((label, fs.render_vec(f, t, px=40)))
        blocks.append((role, rows))
    ttf = os.path.join(FONTS, 'SB_Aggro_M.ttf')
    ch, remap, pages, cnt = fs.ue3_bitmap(os.path.join(fs.COOKED, 'VGSBase_LOC_JPN.xxx'), True, 'SubtitleFont')
    rows = [('원본 일본어', fs.render_bitmap(ch, remap, pages, fc.SUB_JP))]
    for label, gap in [('잉크+2px(현재)', 2), ('잉크+1px', 1)]:
        rnd = subfont.Renderer(ttf, 21, 10, gap=gap)
        for t in (S1, S2, S3):
            rows.append((label, fc.bitmap_line(rnd, t)))
    for t in (S1, S2, S3):
        rows.append(('어그로 자체 폭', sub_natural(ttf, t)))
    blocks.append(('③ 자막 — 어그로 M (실제 크기 ×1.6)', rows))

    W = 1150
    H = sum(46 + sum(r[1].height + 6 for r in b[1]) for b in blocks) + 20
    sheet = Image.new('RGB', (W, H), (22, 24, 30))
    d = ImageDraw.Draw(sheet)
    y = 10
    for role, rows in blocks:
        d.text((16, y), role, font=lab, fill=(255, 210, 90))
        y += 40
        prev = None
        for label, im in rows:
            if label != prev:
                d.text((16, y + im.height // 2 - 9), label, font=small, fill=(200, 200, 200))
                prev = label
            sheet.paste(Image.merge('RGB', [im, im, im]), (200, y))
            y += im.height + 6
        d.line([(10, y), (W - 10, y)], fill=(70, 70, 80))
        y += 6
    sheet.save(out)
    print(out, sheet.size)


if __name__ == '__main__':
    main()
