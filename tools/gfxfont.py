"""GFx/SWF DefineFont3 읽기·글리프 추가·다시 쓰기.

DefineFont3(태그 75) 구조(리틀엔디언):
  u16 FontID, u8 flags, u8 lang, u8 name_len, name, u16 NumGlyphs
  오프셋 표(u32 × NumGlyphs, flags&0x08) + u32 CodeTableOffset   ← 표 시작 기준
  글리프 도형들(SHAPE: u8 [NumFillBits:4|NumLineBits:4] + 레코드)
  코드 표(u16 × NumGlyphs, 오름차순)
  flags&0x80(HasLayout): s16 Ascent, Descent, Leading, s16 Advance × n, RECT × n, u16 KerningCount, 커닝(u16 코드×2 + s16)
좌표는 EM 1024 × 20 = 20480 단위, y 아래쪽이 +.
"""
import struct


class BitReader:
    def __init__(self, b, pos=0):
        self.b, self.bit = b, pos * 8

    def u(self, n):
        v = 0
        for _ in range(n):
            byte = self.b[self.bit >> 3]
            v = (v << 1) | ((byte >> (7 - (self.bit & 7))) & 1)
            self.bit += 1
        return v

    def s(self, n):
        v = self.u(n)
        if n and v & (1 << (n - 1)):
            v -= 1 << n
        return v

    def align(self):
        self.bit = (self.bit + 7) & ~7

    @property
    def pos(self):
        return (self.bit + 7) >> 3


class BitWriter:
    def __init__(self):
        self.out = bytearray()
        self.acc = 0
        self.n = 0

    def u(self, v, n):
        for i in range(n - 1, -1, -1):
            self.acc = (self.acc << 1) | ((v >> i) & 1)
            self.n += 1
            if self.n == 8:
                self.out.append(self.acc)
                self.acc = self.n = 0

    def s(self, v, n):
        self.u(v & ((1 << n) - 1), n)

    def align(self):
        if self.n:
            self.u(0, 8 - self.n)

    def bytes(self):
        self.align()
        return bytes(self.out)


def sbits(*vals):
    """부호 있는 값들을 담을 최소 비트 수."""
    n = 1
    for v in vals:
        need = (v.bit_length() if v >= 0 else (~v).bit_length()) + 1
        n = max(n, need)
    return n


def read_rect(b, pos):
    r = BitReader(b, pos)
    nb = r.u(5)
    vals = [r.s(nb) for _ in range(4)]
    return vals, r.pos


def write_rect(xmin, xmax, ymin, ymax):
    w = BitWriter()
    nb = sbits(xmin, xmax, ymin, ymax)
    w.u(nb, 5)
    for v in (xmin, xmax, ymin, ymax):
        w.s(v, nb)
    return w.bytes()


class Font3:
    def __init__(self, body):
        self.id, self.flags, self.lang, nlen = struct.unpack_from('<HBBB', body, 0)
        self.name = body[5:5 + nlen]
        p = 5 + nlen
        n = struct.unpack_from('<H', body, p)[0]
        p += 2
        wide = self.flags & 0x08
        assert self.flags & 0x04, '와이드 코드가 아님'
        osz = 4 if wide else 2
        tstart = p
        offs = list(struct.unpack_from('<%d%s' % (n + 1, 'I' if wide else 'H'), body, p))
        code_off = offs[n]
        self.shapes = [body[tstart + offs[i]: tstart + (offs[i + 1] if i + 1 < n else code_off)] for i in range(n)]
        p = tstart + code_off
        self.codes = list(struct.unpack_from('<%dH' % n, body, p))
        p += 2 * n
        self.layout = None
        if self.flags & 0x80:
            asc, desc, lead = struct.unpack_from('<hhh', body, p)
            p += 6
            adv = list(struct.unpack_from('<%dh' % n, body, p))
            p += 2 * n
            rects = []
            for _ in range(n):
                start = p
                _, p = read_rect(body, p)
                rects.append(body[start:p])
            kc = struct.unpack_from('<H', body, p)[0]
            p += 2
            kern = body[p:p + kc * 6]
            p += kc * 6
            self.layout = {'asc': asc, 'desc': desc, 'lead': lead, 'adv': adv, 'rects': rects, 'kc': kc, 'kern': kern}
        self.tail = body[p:]
        self.n = n

    def serialize(self):
        n = len(self.codes)
        order = sorted(range(n), key=lambda i: self.codes[i])
        shapes = [self.shapes[i] for i in order]
        codes = [self.codes[i] for i in order]
        wide = bool(self.flags & 0x08) or (2 * (n + 1) + sum(map(len, shapes))) > 0xFFFF
        osz = 4 if wide else 2
        flags = (self.flags | 0x08) if wide else self.flags
        head = struct.pack('<HBBB', self.id, flags, self.lang, len(self.name)) + self.name + struct.pack('<H', n)
        offs = []
        cur = osz * (n + 1)
        for s in shapes:
            offs.append(cur)
            cur += len(s)
        out = (head + struct.pack('<%d%s' % (n + 1, 'I' if wide else 'H'), *(offs + [cur]))
               + b''.join(shapes) + struct.pack('<%dH' % n, *codes))
        if self.layout is not None:
            L = self.layout
            out += struct.pack('<hhh', L['asc'], L['desc'], L['lead'])
            out += struct.pack('<%dh' % n, *[L['adv'][i] for i in order])
            out += b''.join(L['rects'][i] for i in order)
            out += struct.pack('<H', L['kc']) + L['kern']
        return out + self.tail

    def add(self, code, shape, adv, rect):
        """글리프 하나 추가(이미 있으면 바꿈)."""
        if code in self.codes:
            i = self.codes.index(code)
            self.shapes[i] = shape
            if self.layout:
                self.layout['adv'][i] = adv
                self.layout['rects'][i] = rect
            return
        self.codes.append(code)
        self.shapes.append(shape)
        if self.layout:
            self.layout['adv'].append(adv)
            self.layout['rects'].append(rect)


def shape_from_contours(contours):
    """contours: [[('M',x,y)|('L',x,y)|('Q',cx,cy,x,y), ...], ...] 좌표는 SWF 단위 정수(y 아래 +).
    글꼴 도형: NumFillBits=1, NumLineBits=0, 첫 이동에서 FillStyle0=1 (원본 글리프와 같은 방식)."""
    w = BitWriter()
    w.u(1, 4)
    w.u(0, 4)
    first = True
    cx = cy = 0
    for cont in contours:
        for seg in cont:
            if seg[0] == 'M':
                x, y = seg[1], seg[2]
                nb = sbits(x, y)
                # StyleChangeRecord: TypeFlag0, StateNewStyles0, LineStyle0, FillStyle1, FillStyle0, MoveTo
                w.u(0, 1)
                w.u(0, 1)
                w.u(0, 1)
                w.u(0, 1)
                w.u(1 if first else 0, 1)
                w.u(1, 1)
                w.u(nb, 5)
                w.s(x, nb)
                w.s(y, nb)
                if first:
                    w.u(1, 1)  # FillStyle0 인덱스(NumFillBits=1)
                first = False
                cx, cy = x, y
            elif seg[0] == 'L':
                dx, dy = seg[1] - cx, seg[2] - cy
                if dx == 0 and dy == 0:
                    continue
                nb = max(2, sbits(dx, dy))
                w.u(1, 1)
                w.u(1, 1)
                w.u(nb - 2, 4)
                if dx != 0 and dy != 0:
                    w.u(1, 1)
                    w.s(dx, nb)
                    w.s(dy, nb)
                else:
                    w.u(0, 1)
                    if dx == 0:
                        w.u(1, 1)
                        w.s(dy, nb)
                    else:
                        w.u(0, 1)
                        w.s(dx, nb)
                cx, cy = seg[1], seg[2]
            elif seg[0] == 'Q':
                cdx, cdy = seg[1] - cx, seg[2] - cy
                adx, ady = seg[3] - seg[1], seg[4] - seg[2]
                nb = max(2, sbits(cdx, cdy, adx, ady))
                w.u(1, 1)
                w.u(0, 1)
                w.u(nb - 2, 4)
                for v in (cdx, cdy, adx, ady):
                    w.s(v, nb)
                cx, cy = seg[3], seg[4]
    w.u(0, 6)  # EndShapeRecord
    return w.bytes()


def decode_shape(shape):
    """글리프 도형 → contours([('M',x,y),('L',x,y),('Q',cx,cy,x,y)…])와 스타일 변경 기록."""
    r = BitReader(shape)
    nf, nl = r.u(4), r.u(4)
    contours = []
    cur = None
    x = y = 0
    styles = []
    while True:
        if r.u(1) == 0:
            flags = r.u(5)
            if flags == 0:
                break
            if flags & 1:
                nb = r.u(5)
                x, y = r.s(nb), r.s(nb)
                cur = [('M', x, y)]
                contours.append(cur)
            st = {}
            if flags & 2:
                st['f0'] = r.u(nf)
            if flags & 4:
                st['f1'] = r.u(nf)
            if flags & 8:
                st['l'] = r.u(nl)
            styles.append(st)
        else:
            straight = r.u(1)
            nb = r.u(4) + 2
            if straight:
                if r.u(1):
                    dx, dy = r.s(nb), r.s(nb)
                elif r.u(1):
                    dx, dy = 0, r.s(nb)
                else:
                    dx, dy = r.s(nb), 0
                x, y = x + dx, y + dy
                cur.append(('L', x, y))
            else:
                cdx, cdy, adx, ady = r.s(nb), r.s(nb), r.s(nb), r.s(nb)
                cx, cy = x + cdx, y + cdy
                x, y = cx + adx, cy + ady
                cur.append(('Q', cx, cy, x, y))
    return contours, styles


def signed_area(cont):
    pts = [(s[-2], s[-1]) for s in cont]
    a = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2
