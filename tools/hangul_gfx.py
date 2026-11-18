"""TTF/OTF 글리프 → GFx DefineFont3 도형 변환, fonts_en 에 한글 넣기.

크기·위치: 대상 글꼴의 '国' 잉크 상자에 TTF '국' 잉크 상자의 높이·세로 가운데를 맞춘다(전 글자 같은 변환).
가로는 '国' 진행 폭 가운데에 TTF 진행 폭 가운데를 맞춘다. 진행 폭은 '国'과 같게.
바깥 윤곽 넓이가 양수(y 아래+ 기준)가 되도록 필요하면 윤곽 방향을 뒤집는다.
"""
import os
import sys

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.cu2qu import curve_to_quadratic

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxfont  # noqa: E402


class SegPen(BasePen):
    def __init__(self, glyphset, tf):
        super().__init__(glyphset)
        self.tf = tf
        self.contours = []
        self.cur = None
        self.last = None

    def _p(self, pt):
        return self.tf(pt[0], pt[1])

    def _moveTo(self, pt):
        self.cur = [('M',) + self._p(pt)]
        self.contours.append(self.cur)
        self.start = pt
        self.last = pt

    def _lineTo(self, pt):
        self.cur.append(('L',) + self._p(pt))
        self.last = pt

    def _qCurveToOne(self, p1, p2):
        self.cur.append(('Q',) + self._p(p1) + self._p(p2))
        self.last = p2

    def _curveToOne(self, p1, p2, p3):
        quads = curve_to_quadratic([self.last, p1, p2, p3], 1.0)
        # quads: [on, off, (off...), on] → 암시적 on-curve 를 넣어 Q 로 쪼갬
        pts = quads[1:]
        for i in range(len(pts) - 1):
            off = pts[i]
            if i + 1 == len(pts) - 1:
                on = pts[i + 1]
            else:
                nxt = pts[i + 1]
                on = ((off[0] + nxt[0]) / 2, (off[1] + nxt[1]) / 2)
            self._qCurveToOne(off, on)
        self.last = p3

    def _closePath(self):
        if self.last != self.start:
            self._lineTo(self.start)

    _endPath = _closePath


def ink_box(contours):
    xs = [s[-2] for c in contours for s in c]
    ys = [s[-1] for c in contours for s in c]
    return min(xs), max(xs), min(ys), max(ys)


def orient(contours):
    if not contours:
        return contours
    areas = [gfxfont.signed_area(c) for c in contours]
    big = max(range(len(areas)), key=lambda i: abs(areas[i]))
    if areas[big] > 0:
        return contours
    out = []
    for c in contours:
        pts = []
        # 점 목록으로 바꿔 거꾸로 이어 붙인다
        start = (c[0][1], c[0][2])
        segs = []
        prev = start
        for s in c[1:]:
            segs.append((prev, s))
            prev = (s[-2], s[-1])
        rc = [('M',) + prev]
        for p0, s in reversed(segs):
            if s[0] == 'L':
                rc.append(('L',) + p0)
            else:
                rc.append(('Q', s[1], s[2]) + p0)
        out.append(rc)
    return out


class HangulSource:
    def __init__(self, path):
        self.font = TTFont(path, fontNumber=0)
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font['hmtx']

    def raw(self, ch, tf):
        name = self.cmap[ord(ch)]
        pen = SegPen(self.gs, tf)
        self.gs[name].draw(pen)
        return pen.contours, self.hmtx[name][0]


def make_transform(src, ref_box, ref_adv, height_ratio=1.0, dx=None):
    """ref_box: 대상 '国' (xmin,xmax,ymin,ymax) SWF 단위(y 아래+).
    dx=None 이면 TTF 진행 폭 가운데를 ref_adv 가운데에 맞춤(고정 폭). 숫자면 그만큼만 가로로 옮김.
    반환: (tf, s)"""
    ident = lambda x, y: (x, y)
    c, adv = src.raw('국', ident)
    xmin, xmax, ymin, ymax = ink_box(c)
    rh = ref_box[3] - ref_box[2]
    s = rh / (ymax - ymin) * height_ratio
    ref_cy = (ref_box[2] + ref_box[3]) / 2  # y 아래+
    src_cy = (ymin + ymax) / 2              # y 위+
    dy = ref_cy + src_cy * s                # y' = -y*s + dy
    if dx is None:
        dx = ref_adv / 2 - adv * s / 2

    def tf(x, y):
        return (int(round(x * s + dx)), int(round(-y * s + dy)))
    tf.s = s
    return tf


def capped(src, ch, tf, cap):
    """cap=(y_from, y_top): TTF 좌표에서 글자 위 끝이 y_top 보다 높으면 y_from 위쪽만 세로로 눌러 위 끝을 y_top 에 맞춤.
    GFx 가 작은 글씨를 픽셀 격자에 맞출 때 ㅊ·ㅎ 꼭지(어그로 위 끝 748~769, 보통 725)를 2px 키워 글자가 커 보이는 문제 대책."""
    if not cap:
        return tf
    from fontTools.pens.boundsPen import BoundsPen
    bp = BoundsPen(src.gs)
    src.gs[src.cmap[ord(ch)]].draw(bp)
    if not bp.bounds:
        return tf
    top = bp.bounds[3]
    y_from, y_top = cap
    if top <= y_top:
        return tf
    k = (y_top - y_from) / (top - y_from)

    def tf2(x, y):
        return tf(x, y if y <= y_from else y_from + (y - y_from) * k)
    tf2.s = tf.s
    return tf2


def glyph(src, ch, tf, cap=None, box=None):
    """box=(y_bottom, y_top) TTF 단위: 면적 0인 보이지 않는 윤곽을 위·아래에 넣어 모든 글자의 크기 상자를 같게 만듦.
    (GFx 가 글자마다 위·아래 끝을 픽셀에 맞추다 꼭지가 솟은 ㅊ·ㅎ 만 2px 커지는 문제를, 모양을 안 바꾸고 막는 안)"""
    tf = capped(src, ch, tf, cap)
    c, adv = src.raw(ch, tf)
    c = orient(c)
    if box:
        for yy in box:
            x, y = tf(adv / 2, yy)
            c = c + [[('M', x, y), ('L', x + 1, y), ('L', x, y)]]
    return gfxfont.shape_from_contours(c)


def add_to_font(f, src, chars, height_ratio=1.0, mode='fixed', track=0.0, space=None, cap=None, box=None):
    """mode='fixed': 진행 폭 = '国' 폭(가운데 정렬)
    mode='natural': 진행 폭 = TTF 자체 폭 × 배율 × (1+track), 줄어든 만큼 글리프를 반씩 왼쪽으로(가운데 유지)
    space: None 이면 띄어쓰기 그대로, 'ttf' 면 TTF 띄어쓰기 폭 × 배율로 바꿈"""
    ref = ord('国') if ord('国') in f.codes else None
    if ref is None:
        return 0
    i = f.codes.index(ref)
    rc, _ = gfxfont.decode_shape(f.shapes[i])
    ref_box = ink_box(rc)  # '国' 잉크 상자(매개변수 box 와 이름이 겹쳐 엉뚱한 윤곽이 붙었던 버그, 11/06 고침)
    adv = f.layout['adv'][i] if f.layout else 20480
    empty_rect = gfxfont.write_rect(0, 0, 0, 0)
    tf_fixed = make_transform(src, ref_box, adv, height_ratio)
    s = tf_fixed.s
    n = 0
    for ch in chars:
        if ord(ch) not in src.cmap:
            continue
        if mode == 'fixed':
            f.add(ord(ch), glyph(src, ch, tf_fixed, cap, box), adv, empty_rect)
        else:
            nat = src.hmtx[src.cmap[ord(ch)]][0] * s
            a = nat * (1 + track)
            tf = make_transform(src, ref_box, adv, height_ratio, dx=(a - nat) / 2)
            f.add(ord(ch), glyph(src, ch, tf, cap, box), int(round(a)), empty_rect)
        n += 1
    if space == 'ttf' and f.layout and 32 in f.codes:
        f.layout['adv'][f.codes.index(32)] = int(round(src.hmtx[src.cmap[32]][0] * s))
    return n
