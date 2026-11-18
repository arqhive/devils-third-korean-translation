"""모든 패키지의 Texture2D 목록(크기·형식·LOD 그룹·데이터 위치)을 만들고, UI 그룹 텍스처는 썸네일로 꺼낸다.

- 프로퍼티(SizeX/SizeY/Format/LODGroup)를 읽는다.
- 패키지 안에 첫 mip 데이터가 있으면(벌크 머리 크기 = 계산 크기) GX2 tileMode 4 로 풀어 PNG(긴 변 256) 저장.
- 데이터가 tfc(텍스처 캐시)에 있으면 위치만 기록.
출력: work/survey/textures.json, work/survey/uitex/<패키지>__<이름>.png
사용: python -I tools/ui_textures.py [프로세스 수]
"""
import json
import os
import struct
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import texdec  # noqa: E402
import ue3font  # noqa: E402
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402

ROOT = os.path.dirname(HERE)
COOKED = os.path.join(ROOT, 'Devils Third [Game] [0005000010138f00]', 'content', 'DevilsThirdGame', 'CookedWiiU')
OUT = os.path.join(ROOT, 'work', 'survey', 'uitex')
GX2 = {'PF_DXT1': (0x31, 8, True), 'PF_DXT3': (0x32, 16, True), 'PF_DXT5': (0x33, 16, True),
       'PF_A8R8G8B8': (0x1A, 4, False), 'PF_G8': (0x01, 1, False)}


def tex_props(b, names):
    net, props, native = ue3font.parse_font(b, names)
    d = {}
    for p in props:
        if p.typ == 'IntProperty':
            d[p.name] = struct.unpack('>i', p.raw)[0]
        elif p.typ == 'ByteProperty' and len(p.raw) == 8:
            d[p.name] = names[struct.unpack('>i', p.raw[:4])[0]]
    return d, len(b) - len(native)


def size_of(fmt, w, h):
    g = GX2.get(fmt)
    if not g:
        return None
    code, bpe, bc = g
    return ((w + 3) // 4) * ((h + 3) // 4) * bpe if bc else w * h * bpe


def one(name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(COOKED, name)
    try:
        raw = open(path, 'rb').read()
        if raw[:4] == b'\x9e\x2a\x83\xc1' and struct.unpack_from('>I', raw, 4)[0] == 0x20000:
            raw = ue3full.unpack(raw)
        pk, body, names, imps, exps = ue3pkg.tables(raw)
    except Exception as e:  # noqa: BLE001
        return name, [{'error': repr(e)}]
    out = []
    for e in exps:
        if e['class'] != 'Texture2D':
            continue
        b = body[e['offset']:e['offset'] + e['size']]
        try:
            d, nat = tex_props(b, names)
        except Exception as ex:  # noqa: BLE001
            out.append({'name': e['name'], 'error': repr(ex)})
            continue
        w, h, fmt = d.get('SizeX'), d.get('SizeY'), d.get('Format', 'PF_DXT1')
        rec = {'name': e['name'], 'w': w, 'h': h, 'fmt': fmt, 'lod': d.get('LODGroup', 'TEXTUREGROUP_World'),
               'inline': False}
        # 네이티브: SourceArt 벌크 머리(16) [+데이터] + mip 수 + mip[0] 벌크 머리(flags, count, size, offset)
        q = nat
        sflags, scount, ssize, soff = struct.unpack_from('>IIII', b, q)
        q += 16 + (ssize if not (sflags & 1) else 0)
        nm = struct.unpack_from('>I', b, q)[0]
        q += 4
        if 0 < nm < 20:
            mflags, mcount, msize, moff = struct.unpack_from('>IIII', b, q)
            q += 16
            rec.update(mip_flags=mflags, mip_size=msize, mip_off=moff, mips=nm)
            if not (mflags & 1) and msize and q + msize <= len(b):
                rec['inline'] = True
                if rec['lod'] == 'TEXTUREGROUP_UI' and fmt in GX2:
                    try:
                        img = texdec.decode(b[q:q + msize], w, h, GX2[fmt][0], 4, 0)
                        im = Image.fromarray(np.ascontiguousarray(img), 'RGBA')
                        im.thumbnail((256, 256))
                        fn = '%s__%s.png' % (name.rsplit('.', 1)[0], e['name'])
                        im.save(os.path.join(OUT, fn))
                        rec['png'] = fn
                    except Exception as ex:  # noqa: BLE001
                        rec['decode_error'] = repr(ex)
        out.append(rec)
    return name, out


def main():
    os.makedirs(OUT, exist_ok=True)
    names = sorted(n for n in os.listdir(COOKED) if n.endswith('.xxx'))
    procs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    res = {}
    with Pool(procs) as p:
        for name, recs in p.imap_unordered(one, names, chunksize=2):
            if recs:
                res[name] = recs
    json.dump(res, open(os.path.join(ROOT, 'work', 'survey', 'textures.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    allr = [r for v in res.values() for r in v]
    print('textures', len(allr), 'ui', sum(1 for r in allr if r.get('lod') == 'TEXTUREGROUP_UI'),
          'png', sum(1 for r in allr if r.get('png')), 'errors', sum(1 for r in allr if 'error' in r or 'decode_error' in r))


if __name__ == '__main__':
    main()
