"""CookedWiiU 전체 패키지의 이름 표만 읽어 클래스·이름 분포를 낸다(조사용).

이름 표는 첫 압축 블록 안에 있으므로 첫 블록만 푼다.
사용: python -I tools/survey_classes.py <CookedWiiU 폴더> <출력.json>
"""
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ue3pkg  # noqa: E402


def first_block(buf, off):
    tag, cs, csz, usz = struct.unpack_from('>4I', buf, off)
    n = (usz + cs - 1) // cs
    c, u = struct.unpack_from('>2I', buf, off + 16)
    return zlib.decompress(buf[off + 16 + n * 8: off + 16 + n * 8 + c])


def names_of(path):
    with open(path, 'rb') as f:
        head = f.read(0x40000)
    if struct.unpack_from('>I', head, 4)[0] == 0x20000:
        head = first_block(head, 0)
        pk = ue3pkg.Pkg(head)
        body = head
    else:
        pk = ue3pkg.Pkg(head)
        if pk.chunks:
            uo, us, co, cs = pk.chunks[0]
            if co + 64 > len(head):
                with open(path, 'rb') as f:
                    f.seek(co)
                    blk = f.read(min(cs, 0x200000))
                first = first_block(blk, 0)
            else:
                with open(path, 'rb') as f:
                    f.seek(co)
                    first = first_block(f.read(0x40000), 0)
            body = bytes(uo) + first
        else:
            body = head
    pk.raw = body
    pk.p = pk.name_off
    out = []
    for _ in range(pk.name_count):
        if pk.p + 4 > len(body):
            break
        out.append(pk.fstr())
        pk.p += 8
    return out


def main(folder, dst):
    res = {}
    for n in sorted(os.listdir(folder)):
        if not n.endswith('.xxx'):
            continue
        try:
            res[n] = names_of(os.path.join(folder, n))
        except Exception as e:  # noqa: BLE001
            res[n] = ['!ERR ' + repr(e)]
    json.dump(res, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
    err = [k for k, v in res.items() if v and v[0].startswith('!ERR')]
    print('packages', len(res), 'errors', len(err))
    for k in ('SwfMovie', 'Font', 'Texture2D', 'SoundNodeWave', 'TextureMovie'):
        print(k, sum(1 for v in res.values() if k in v))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
