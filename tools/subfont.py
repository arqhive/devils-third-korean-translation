"""자막 폰트(UE3 Font SubtitleFont)에 한글 넣기 — 안 쓰는 한자 칸을 한글로 덮어쓴다.

- 칸은 잉크에 딱 맞춘 상자(StartU, StartV, USize, VSize), VerticalOffset = 줄 위쪽에서 잉크 위까지.
- 한글 크기: TTF '국' 잉크 높이를 원본 '国' 높이에 맞추고, '국' 위쪽을 '国'의 VerticalOffset 에 맞춘다.
- 칸 너비 USize = 잉크 너비 + 간격(gap). 줄 간격·진행은 USize 를 따른다.
- 페이지는 고친 4×4 블록만 다시 인코딩(etcpak BC3)해서 나머지 블록은 원본 그대로 둔다.
"""
import os
import struct
import sys

import etcpak
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gtx_lib  # noqa: E402
import ue3font  # noqa: E402
import ue3tex  # noqa: E402


class Renderer:
    def __init__(self, ttf, ref_h, ref_top, gap=2):
        self.ttf = ttf
        self.gap = gap
        # 크기 맞추기: '국' 잉크 높이 == ref_h
        size = ref_h
        for _ in range(30):
            f = ImageFont.truetype(ttf, size)
            box = self._ink(f, '국')
            h = box[3] - box[1] + 1
            if h == ref_h:
                break
            size = size * ref_h / h
        self.font = ImageFont.truetype(ttf, round(size) if abs(size - round(size)) < 1e-6 else size)
        box = self._ink(self.font, '국')
        self.line_top = box[1] - ref_top  # 캔버스 y → 줄 y 변환

    @staticmethod
    def _ink(font, ch, canvas=96, base=72):
        im = Image.new('L', (canvas, canvas), 0)
        ImageDraw.Draw(im).text((8, base), ch, font=font, fill=255, anchor='ls')
        a = np.asarray(im)
        ys, xs = np.nonzero(a > 0)
        return xs.min(), ys.min(), xs.max(), ys.max()

    def glyph(self, ch):
        im = Image.new('L', (96, 96), 0)
        ImageDraw.Draw(im).text((8, 72), ch, font=self.font, fill=255, anchor='ls')
        a = np.asarray(im)
        ys, xs = np.nonzero(a > 0)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        crop = a[y0:y1 + 1, x0:x1 + 1]
        return crop, int(y0 - self.line_top)


def glyph_natural(rnd, ch):
    """(crop, top, lsb, adv): lsb = 원점에서 잉크 왼쪽까지 px, adv = TTF 진행 폭 px(반올림)."""
    im = Image.new('L', (128, 96), 0)
    ImageDraw.Draw(im).text((16, 72), ch, font=rnd.font, fill=255, anchor='ls')
    a = np.asarray(im)
    adv = int(round(rnd.font.getlength(ch)))
    ys, xs = np.nonzero(a > 0)
    if not len(xs):
        return None, 0, 0, adv
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    return a[y0:y1 + 1, x0:x1 + 1], int(y0 - rnd.line_top), int(x0 - 16), adv


class BlockAlloc:
    """페이지별 4×4 블록 점유표에서 빈 사각형을 첫 맞춤으로 찾는다."""

    def __init__(self, sizes):
        self.occ = [np.zeros((h // 4, w // 4), bool) for (w, h) in sizes]

    def mark(self, ti, x, y, w, h, pad=1):
        bx0, by0 = max(0, (x - pad) // 4), max(0, (y - pad) // 4)
        bx1, by1 = (x + w + pad + 3) // 4, (y + h + pad + 3) // 4
        self.occ[ti][by0:by1, bx0:bx1] = True

    def find(self, w, h, pad=1):
        bw, bh = (w + pad + 3) // 4, (h + pad + 3) // 4
        for ti, o in enumerate(self.occ):
            H, W = o.shape
            if bw > W or bh > H:
                continue
            s = np.pad(o.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
            tot = s[bh:, bw:] - s[:-bh, bw:] - s[bh:, :-bw] + s[:-bh, :-bw]
            ys, xs = np.nonzero(tot == 0)
            if len(ys):
                by, bx = ys[0], xs[0]
                o[by:by + bh, bx:bx + bw] = True
                return ti, bx * 4, by * 4, bw * 4, bh * 4
        return None


def glyph_hinted(hint, rnd, ch):
    """vhint 로 그린 한글: glyph_natural 과 같은 (crop, top, lsb, adv). top 은 줄 좌표(rnd.line_top 기준)."""
    a, top, left, adv = hint.render(ch)
    adv = int(round(adv))
    if a is None:
        return None, 0, 0, adv
    ys, xs = np.nonzero(a > 0)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    crop = np.clip(np.rint(a[y0:y1 + 1, x0:x1 + 1]), 0, 255).astype(np.uint8)
    # glyph_natural 은 기준선을 캔버스 72 에 두고 top = 캔버스 y - line_top
    return crop, int(72 + top + y0 - rnd.line_top), int(left + x0), adv


def inject_natural(font_exp, names, page_exps, page_sizes, chars, ttf, keep, redraw='“”‘’', ref='国', hint=False):
    """원래 폭 방식: 칸 너비 USize = 어그로 TTF 진행 폭, 잉크는 칸 안 lsb 위치.
    쓰이는 글자(keep)·한자 아닌 글자의 칸은 그대로 두고(그 블록은 다시 인코딩 안 함), 빈 블록에 새 칸을 잡는다.
    chars(한글)은 안 쓰는 한자 칸 번호를 물려받고, redraw 글자와 띄어쓰기는 자기 칸 번호에 새 칸을 잡는다.
    반환: (새 font_exp, 새 page_exps, 보고, 페이지 그림)"""
    net, props, native = ue3font.parse_font(font_exp, names)
    cprop = [p for p in props if p.name == 'Characters'][0]
    chars_tbl = ue3font.chars_of(cprop.raw)
    pairs, rest = ue3font.remap_of(native)
    remap = dict(pairs)
    rsu, rsv, rus, rvs, rti, rvo = chars_tbl[remap[ord(ref)]]
    rnd = Renderer(ttf, rvs, rvo)
    hinter = None
    if hint:
        import vhint
        hinter = vhint.OHint(rnd.font.size, [c for c in chars if 0xAC00 <= ord(c) <= 0xD7A3], ttf)

    pages = [ue3tex.decode_page(p, w, h) for p, (w, h) in zip(page_exps, page_sizes)]
    imgs = [pg[0].copy() for pg in pages]
    dirty = [np.zeros((h // 4, w // 4), bool) for (w, h) in page_sizes]
    alloc = BlockAlloc(page_sizes)

    is_donor = lambda code: 0x4E00 <= code <= 0x9FFF and chr(code) not in keep
    donors = sorted(idx for code, idx in remap.items() if is_donor(code))
    for code, idx in remap.items():
        if not is_donor(code):
            su, sv, us, vs, ti, vo = chars_tbl[idx]
            alloc.mark(ti, su, sv, us, vs)
    need = [c for c in chars if ord(c) not in remap]
    if len(need) > len(donors):
        raise RuntimeError('칸 번호 부족: 필요 %d, 남는 한자 %d' % (len(need), len(donors)))

    report = []

    def place(ch, idx):
        if hinter is not None and 0xAC00 <= ord(ch) <= 0xD7A3:
            crop, top, lsb, adv = glyph_hinted(hinter, rnd, ch)
        else:
            crop, top, lsb, adv = glyph_natural(rnd, ch)
        if crop is None:  # 띄어쓰기: 빈 칸, 높이·세로 위치는 원래 값(36px = 가장 높은 칸이라 줄 높이에 쓰일 수 있음)
            w, lsb = 0, 0
            h, top = chars_tbl[idx][3], chars_tbl[idx][5]
        else:
            h, w = crop.shape
        lsb = max(0, lsb)
        cw = max(adv, lsb + w)
        got = alloc.find(cw, h)
        if got is None:
            raise RuntimeError('페이지 빈자리 없음: %s' % ch)
        ti, x, y, bw, bh = got
        img = imgs[ti]
        img[y:y + bh, x:x + bw, 3] = 0
        img[y:y + bh, x:x + bw, :3] = 255
        if crop is not None:
            img[y:y + h, x + lsb:x + lsb + w, 3] = crop
        dirty[ti][y // 4:(y + bh) // 4, x // 4:(x + bw) // 4] = True
        chars_tbl[idx] = [x, y, cw, h, ti, top]
        report.append((ch, ti, x, y, cw, h, top))

    for ch in ' ' + redraw:
        if ord(ch) in remap:
            place(ch, remap[ord(ch)])
    donor_codes = {idx: code for code, idx in remap.items()}
    for ch in need:
        idx = donors.pop(0)
        del remap[donor_codes[idx]]
        remap[ord(ch)] = idx
        place(ch, idx)

    cprop.raw = ue3font.chars_raw(chars_tbl)
    new_native = ue3font.remap_raw(sorted(remap.items()), rest)
    names_idx = {n: i for i, n in enumerate(names)}
    new_font = ue3font.build_font(net, props, new_native, names_idx)

    new_pages = []
    for k, (pe, (w, h)) in enumerate(zip(page_exps, page_sizes)):
        if not dirty[k].any():
            new_pages.append(pe)
            continue
        _, off, size = pages[k]
        lin = gtx_lib.deswizzle(pe[off:off + size], w // 4, 16).copy()
        enc = etcpak.compress_bc3(np.ascontiguousarray(imgs[k]).tobytes(), w, h)
        enc = np.frombuffer(enc, np.uint8).reshape(h // 4, w // 4, 16)
        lin[dirty[k]] = enc[dirty[k]]
        new_pages.append(pe[:off] + gtx_lib.swizzle(lin) + pe[off + size:])
    return new_font, new_pages, report, imgs


def pad_cells(font_exp, names, page_exps, page_sizes, chars, left):
    """11/18 사용자 「해! 가 너무 딱 붙어 있어」: chars(「!」「?」) 칸을 빈 블록에 다시 잡아 잉크 왼쪽에 left px 빈칸을 둔다.
    칸 번호·CharRemap·칸 수는 그대로, 그 글자의 Characters 항목(StartU·StartV·USize·TextureIndex)만 바뀐다.
    원래 칸 그림은 지우지 않는다(다른 글자가 같은 블록을 쓸 수 있음)."""
    net, props, native = ue3font.parse_font(font_exp, names)
    cprop = [p for p in props if p.name == 'Characters'][0]
    tbl = ue3font.chars_of(cprop.raw)
    remap = dict(ue3font.remap_of(native)[0])
    pages = [ue3tex.decode_page(p, w, h) for p, (w, h) in zip(page_exps, page_sizes)]
    imgs = [pg[0].copy() for pg in pages]
    dirty = [np.zeros((h // 4, w // 4), bool) for (w, h) in page_sizes]
    alloc = BlockAlloc(page_sizes)
    for c in tbl:
        if c[2] > 0 and c[3] > 0:
            alloc.mark(c[4], c[0], c[1], c[2], c[3])
    report = []
    for ch in chars:
        idx = remap[ord(ch)]
        x, y, w, h, ti, vo = tbl[idx]
        glyph = imgs[ti][y:y + h, x:x + w].copy()
        nw = w + left
        got = alloc.find(nw, h)
        if got is None:
            raise RuntimeError('빈자리 없음: %s' % ch)
        nti, nx, ny, bw, bh = (int(v) for v in got)
        imgs[nti][ny:ny + bh, nx:nx + bw, 3] = 0
        imgs[nti][ny:ny + bh, nx:nx + bw, :3] = 255
        imgs[nti][ny:ny + h, nx + left:nx + left + w] = glyph
        dirty[nti][ny // 4:(ny + bh + 3) // 4, nx // 4:(nx + bw + 3) // 4] = True
        alloc.mark(nti, nx, ny, nw, h)
        tbl[idx] = [nx, ny, nw, h, nti, vo]
        report.append((ch, (x, y, w, ti), (nx, ny, nw, nti)))
    cprop.raw = ue3font.chars_raw(tbl)
    names_idx = {n: i for i, n in enumerate(names)}
    new_font = ue3font.build_font(net, props, native, names_idx)
    assert len(new_font) == len(font_exp)
    new_pages = []
    for k, ((img, off, size), pe, (w, h)) in enumerate(zip(pages, page_exps, page_sizes)):
        if not dirty[k].any():
            new_pages.append(pe)
            continue
        lin = gtx_lib.deswizzle(pe[off:off + size], w // 4, 16).copy()
        enc = np.frombuffer(etcpak.compress_bc3(np.ascontiguousarray(imgs[k]).tobytes(), w, h), np.uint8).reshape(h // 4, w // 4, 16)
        lin[dirty[k]] = enc[dirty[k]]
        new_pages.append(pe[:off] + gtx_lib.swizzle(lin) + pe[off + size:])
    return new_font, new_pages, report


def append_cells(font_exp, names, page_exp, page_size, chars, ttf, ref_h, ref_top):
    """칸이 줄 높이 통째(VerticalOffset 0)인 작은 글꼴(SkipFont)에 글자를 덧붙인다(칸 수가 늘어남).
    '국' 잉크 높이 = ref_h, 잉크 위 = 칸 위에서 ref_top. 칸 너비 = TTF 진행 폭. 페이지 하나에서 빈 블록을 찾음."""
    net, props, native = ue3font.parse_font(font_exp, names)
    cprop = [p for p in props if p.name == 'Characters'][0]
    tbl = ue3font.chars_of(cprop.raw)
    pairs, rest = ue3font.remap_of(native)
    remap = dict(pairs)
    cell_h = max(c[3] for c in tbl)
    rnd = Renderer(ttf, ref_h, ref_top)
    w, h = page_size
    img, off, size = ue3tex.decode_page(page_exp, w, h)
    img = img.copy()
    alloc = BlockAlloc([page_size])
    for c in tbl:
        alloc.mark(0, c[0], c[1], c[2], c[3])
    dirty = np.zeros((h // 4, w // 4), bool)
    report = []
    for ch in chars:
        if ord(ch) in remap:
            continue
        crop, top, lsb, adv = glyph_natural(rnd, ch)
        gh, gw = crop.shape
        lsb = max(0, lsb)
        cw = max(adv, lsb + gw)
        got = alloc.find(cw, cell_h)
        if got is None:
            raise RuntimeError('SkipFont 빈자리 없음: %s' % ch)
        _, x, y, bw, bh = got
        img[y:y + bh, x:x + bw, 3] = 0
        img[y:y + bh, x:x + bw, :3] = 255
        img[y + top:y + top + gh, x + lsb:x + lsb + gw, 3] = crop
        dirty[y // 4:(y + bh) // 4, x // 4:(x + bw) // 4] = True
        remap[ord(ch)] = len(tbl)
        tbl.append([x, y, cw, cell_h, 0, 0])
        report.append((ch, x, y, cw, cell_h, top))
    cprop.raw = ue3font.chars_raw(tbl)
    names_idx = {n: i for i, n in enumerate(names)}
    new_font = ue3font.build_font(net, props, ue3font.remap_raw(sorted(remap.items()), rest), names_idx)
    lin = gtx_lib.deswizzle(page_exp[off:off + size], w // 4, 16).copy()
    enc = np.frombuffer(etcpak.compress_bc3(np.ascontiguousarray(img).tobytes(), w, h), np.uint8).reshape(h // 4, w // 4, 16)
    lin[dirty] = enc[dirty]
    new_page = page_exp[:off] + gtx_lib.swizzle(lin) + page_exp[off + size:]
    return new_font, new_page, report, img


def reuse_cells(font_exp, names, page_exp, page_size, pairs, ttf, ref_h, ref_top):
    """SkipFont 칸 수를 늘리지 않고, 안 쓰는 글자 칸(pairs 의 옛 글자)을 새 글자로 다시 그린다.
    pairs: [(옛 글자, 새 글자), ...]. 칸 표·CharRemap 개수·익스포트 크기는 원본과 같다."""
    net, props, native = ue3font.parse_font(font_exp, names)
    cprop = [p for p in props if p.name == 'Characters'][0]
    tbl = ue3font.chars_of(cprop.raw)
    rpairs, rest = ue3font.remap_of(native)
    remap = dict(rpairs)
    rnd = Renderer(ttf, ref_h, ref_top)
    w, h = page_size
    img, off, size = ue3tex.decode_page(page_exp, w, h)
    img = img.copy()
    dirty = np.zeros((h // 4, w // 4), bool)
    report = []
    for old, ch in pairs:
        idx = remap.pop(ord(old))
        x, y, cw, chh = tbl[idx][:4]
        crop, top, lsb, adv = glyph_natural(rnd, ch)
        gh, gw = crop.shape
        lsb = max(0, lsb)
        if lsb + gw > cw:
            lsb = max(0, (cw - gw) // 2)
        assert lsb + gw <= cw and top + gh <= chh, (ch, lsb, gw, cw, top, gh, chh)
        img[y:y + chh, x:x + cw, 3] = 0
        img[y:y + chh, x:x + cw, :3] = 255
        img[y + top:y + top + gh, x + lsb:x + lsb + gw, 3] = crop
        dirty[y // 4:(y + chh + 3) // 4, x // 4:(x + cw + 3) // 4] = True
        remap[ord(ch)] = idx
        report.append((old, ch, idx, x, y, cw, chh, adv, gw))
    names_idx = {n: i for i, n in enumerate(names)}
    new_font = ue3font.build_font(net, props, ue3font.remap_raw(sorted(remap.items()), rest), names_idx)
    assert len(new_font) == len(font_exp)
    lin = gtx_lib.deswizzle(page_exp[off:off + size], w // 4, 16).copy()
    enc = np.frombuffer(etcpak.compress_bc3(np.ascontiguousarray(img).tobytes(), w, h), np.uint8).reshape(h // 4, w // 4, 16)
    lin[dirty] = enc[dirty]
    new_page = page_exp[:off] + gtx_lib.swizzle(lin) + page_exp[off + size:]
    assert len(new_page) == len(page_exp)
    return new_font, new_page, report, img


def inject(font_exp, names, page_exps, page_sizes, chars, ttf, keep=set(), gap=2, ref='国'):
    """font_exp: SubtitleFont 익스포트 바이트, page_exps: 텍스처 익스포트 바이트 목록(Textures 순서),
    page_sizes: [(w,h)…], chars: 넣을 글자들, keep: 지우면 안 되는 글자(원문에 쓰이는 글자 등).
    반환: (새 font_exp, 새 page_exps, 보고)"""
    net, props, native = ue3font.parse_font(font_exp, names)
    cprop = [p for p in props if p.name == 'Characters'][0]
    chars_tbl = ue3font.chars_of(cprop.raw)
    pairs, rest = ue3font.remap_of(native)
    remap = dict(pairs)
    rsu, rsv, rus, rvs, rti, rvo = chars_tbl[remap[ord(ref)]]
    rnd = Renderer(ttf, rvs, rvo, gap)

    pages = [ue3tex.decode_page(p, w, h) for p, (w, h) in zip(page_exps, page_sizes)]
    imgs = [pg[0].copy() for pg in pages]
    dirty = [np.zeros((h // 4, w // 4), bool) for (w, h) in page_sizes]

    used_idx = {}
    donors = []
    for code, idx in remap.items():
        c = chr(code)
        if 0x4E00 <= code <= 0x9FFF and c not in keep and c not in chars:
            donors.append((code, idx))
    donors.sort(key=lambda x: x[1])
    report = []
    for ch in chars:
        if ord(ch) in remap:
            continue  # 이미 있음(ASCII 등)
        crop, top = rnd.glyph(ch)
        h, w = crop.shape
        need_w = w + gap
        pick = None
        for k, (code, idx) in enumerate(donors):
            su, sv, us, vs, ti, vo = chars_tbl[idx]
            if us >= need_w and vs >= h:
                pick = k
                break
        if pick is None:
            raise RuntimeError('넣을 칸이 없음: %s' % ch)
        code, idx = donors.pop(pick)
        su, sv, us, vs, ti, vo = chars_tbl[idx]
        img = imgs[ti]
        img[sv:sv + vs, su:su + us, 3] = 0
        img[sv:sv + h, su:su + w, 3] = crop
        img[sv:sv + vs, su:su + us, :3] = 255
        dirty[ti][sv // 4:(sv + vs + 3) // 4, su // 4:(su + us + 3) // 4] = True
        chars_tbl[idx] = [su, sv, need_w, h, ti, top]
        del remap[code]
        remap[ord(ch)] = idx
        report.append((ch, chr(code), ti, su, sv, need_w, h, top))

    cprop.raw = ue3font.chars_raw(chars_tbl)
    new_native = ue3font.remap_raw(sorted(remap.items()), rest)
    names_idx = {n: i for i, n in enumerate(names)}
    new_font = ue3font.build_font(net, props, new_native, names_idx)

    new_pages = []
    for k, (pe, (w, h)) in enumerate(zip(page_exps, page_sizes)):
        if not dirty[k].any():
            new_pages.append(pe)
            continue
        _, off, size = pages[k]
        lin = gtx_lib.deswizzle(pe[off:off + size], w // 4, 16).copy()
        enc = etcpak.compress_bc3(np.ascontiguousarray(imgs[k]).tobytes(), w, h)
        enc = np.frombuffer(enc, np.uint8).reshape(h // 4, w // 4, 16)
        lin[dirty[k]] = enc[dirty[k]]
        sw = gtx_lib.swizzle(lin)
        new_pages.append(pe[:off] + sw + pe[off + size:])
    return new_font, new_pages, report, imgs
