"""GFx 무비 안 글상자(DefineEditText)·정적 글(DefineText)·가져온 글꼴 목록.

사용: python -I tools/swf_text.py <gfx 폴더> <출력.json>
"""
import glob
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxfont  # noqa: E402
import swf_tags  # noqa: E402


def cstr(b, p):
    e = b.index(b'\0', p)
    return b[p:e].decode('utf-8', 'replace'), e + 1


def sub_tags(b, p, end):
    while p < end:
        cl = struct.unpack_from('<H', b, p)[0]
        code, ln = cl >> 6, cl & 0x3F
        p += 2
        if ln == 0x3F:
            ln = struct.unpack_from('<I', b, p)[0]
            p += 4
        yield code, p, ln
        p += ln
        if code == 0:
            break


def walk(b, start, end, sprite=None):
    for code, p, ln in sub_tags(b, start, end):
        yield code, p, ln, sprite
        if code == 39:  # DefineSprite
            sid = struct.unpack_from('<H', b, p)[0]
            yield from walk(b, p + 4, p + ln, sid)


def edit_text(body):
    cid = struct.unpack_from('<H', body, 0)[0]
    (xmin, xmax, ymin, ymax), p = gfxfont.read_rect(body, 2)
    f1, f2 = body[p], body[p + 1]
    p += 2
    d = {'id': cid, 'x': xmin / 20, 'y': ymin / 20, 'w': (xmax - xmin) / 20, 'h': (ymax - ymin) / 20,
         'wordwrap': bool(f1 & 0x40), 'multiline': bool(f1 & 0x20), 'readonly': bool(f1 & 0x08),
         'autosize': bool(f2 & 0x40), 'html': bool(f2 & 0x02), 'outlines': bool(f2 & 0x01)}
    if f1 & 0x01:
        d['font_id'] = struct.unpack_from('<H', body, p)[0]
        p += 2
    if f2 & 0x80:
        d['font_class'], p = cstr(body, p)
    if f1 & 0x01 or f2 & 0x80:
        d['size'] = struct.unpack_from('<H', body, p)[0] / 20
        p += 2
    if f1 & 0x04:
        d['color'] = body[p:p + 4].hex()
        p += 4
    if f1 & 0x02:
        d['maxlen'] = struct.unpack_from('<H', body, p)[0]
        p += 2
    if f2 & 0x20:
        al, lm, rm, ind, lead = struct.unpack_from('<BHHHh', body, p)
        d.update(align=['left', 'right', 'center', 'justify'][al] if al < 4 else al,
                 lmargin=lm / 20, rmargin=rm / 20, indent=ind / 20, leading=lead / 20)
        p += 9
    d['var'], p = cstr(body, p)
    if f1 & 0x80:
        d['text'], p = cstr(body, p)
    return d


def movie_info(g):
    fonts = {}
    imports = []
    edits = []
    statics = 0
    names = {}
    exports = {}
    nbits = g[8] >> 3
    start = 8 + (5 + nbits * 4 + 7) // 8 + 4
    declared = struct.unpack_from('<I', g, 4)[0]
    for code, p, ln, spr in walk(g, start, declared):
        body = g[p:p + ln]
        if code in (57, 71):  # ImportAssets / ImportAssets2
            url, q = cstr(body, 0)
            if code == 71:
                q += 2
            n = struct.unpack_from('<H', body, q)[0]
            q += 2
            for _ in range(n):
                tid = struct.unpack_from('<H', body, q)[0]
                nm, q = cstr(body, q + 2)
                imports.append({'url': url, 'id': tid, 'name': nm})
                fonts[tid] = nm
        elif code in (48, 75):
            f = gfxfont.Font3(body) if code == 75 else None
            if f:
                fonts[f.id] = f.name.rstrip(b'\0').decode('utf-8', 'replace')
        elif code == 37:
            d = edit_text(body)
            d['sprite'] = spr
            edits.append(d)
        elif code in (11, 33):
            statics += 1
        elif code == 56:  # ExportAssets
            n = struct.unpack_from('<H', body, 0)[0]
            q = 2
            for _ in range(n):
                tid = struct.unpack_from('<H', body, q)[0]
                nm, q = cstr(body, q + 2)
                exports[tid] = nm
        elif code in (26, 70):  # PlaceObject2/3: 인스턴스 이름
            flags = body[0]
            q = 1
            if code == 70:
                flags2 = body[1]
                q = 2
            depth = struct.unpack_from('<H', body, q)[0]
            q += 2
            if code == 70 and (flags2 & 0x08 or (flags2 & 0x10 and flags & 0x02)):
                pass
            if flags & 0x02:
                cid = struct.unpack_from('<H', body, q)[0]
                q += 2
            else:
                cid = None
            if flags & 0x20 and code == 26:
                # 행렬·색 변환을 건너뛰어야 이름을 읽을 수 있음
                if flags & 0x04:
                    r = gfxfont.BitReader(body, q)
                    if r.u(1):
                        nb = r.u(5); r.s(nb); r.s(nb)
                    if r.u(1):
                        nb = r.u(5); r.s(nb); r.s(nb)
                    nb = r.u(5); r.s(nb); r.s(nb)
                    q = r.pos
                if flags & 0x08:
                    r = gfxfont.BitReader(body, q)
                    ha, hm = r.u(1), r.u(1)
                    nb = r.u(4)
                    for _ in range((4 if ha else 0) + (4 if hm else 0)):
                        r.s(nb)
                    q = r.pos
                if flags & 0x10:
                    q += 2
                nm, q = cstr(body, q)
                if cid is not None:
                    names.setdefault(cid, []).append((spr, nm))
    for d in edits:
        d['font'] = fonts.get(d.get('font_id'), d.get('font_class'))
        d['inst'] = [nm for _, nm in names.get(d['id'], [])]
    return {'imports': imports, 'edits': edits, 'static_texts': statics, 'exports': exports, 'fonts': fonts}


def main(folder, out):
    res = {}
    for f in sorted(glob.glob(os.path.join(folder, '*.gfx'))):
        g = open(f, 'rb').read()
        try:
            res[os.path.basename(f)[:-4]] = movie_info(g)
        except Exception as e:  # noqa: BLE001
            res[os.path.basename(f)[:-4]] = {'error': repr(e)}
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    print('movies', len(res), 'edits', sum(len(v.get('edits', [])) for v in res.values()),
          'errors', sum(1 for v in res.values() if 'error' in v))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
