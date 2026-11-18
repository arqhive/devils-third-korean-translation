"""UE3 통째 압축 패키지(.xxx, 머리 9E2A83C1) 풀기·묶기.

구조(빅엔디언):
  u32 tag=0x9E2A83C1, u32 chunk_size(0x20000), u32 압축 합계, u32 원래 크기
  청크 표: (u32 압축 크기, u32 원래 크기) × ceil(원래 크기 / chunk_size)
  zlib 청크 데이터가 이어지고, 파일 끝은 0x8000 경계까지 0으로 채움

사용:
  python -I tools/ue3full.py unpack <입력.xxx> <출력.upk>
  python -I tools/ue3full.py pack <입력.upk> <출력.xxx> [--level N]
"""
import struct
import sys
import zlib

TAG = 0x9E2A83C1
PAD = 0x8000


def unpack(data: bytes) -> bytes:
    tag, cs, csz, usz = struct.unpack_from('>4I', data, 0)
    if tag != TAG:
        raise ValueError('통째 압축 형식 아님: %08X' % tag)
    n = (usz + cs - 1) // cs
    pos = 16 + n * 8
    out = bytearray()
    for i in range(n):
        c, u = struct.unpack_from('>2I', data, 16 + i * 8)
        block = zlib.decompress(data[pos:pos + c])
        if len(block) != u:
            raise ValueError('청크 %d 크기 다름 %d != %d' % (i, len(block), u))
        out += block
        pos += c
    if len(out) != usz:
        raise ValueError('전체 크기 다름')
    return bytes(out)


def pack(raw: bytes, level: int = 9, chunk: int = 0x20000, pad: bool = True) -> bytes:
    blocks = [raw[i:i + chunk] for i in range(0, len(raw), chunk)]
    comp = [zlib.compress(b, level) for b in blocks]
    head = struct.pack('>4I', TAG, chunk, sum(map(len, comp)), len(raw))
    table = b''.join(struct.pack('>2I', len(c), len(b)) for c, b in zip(comp, blocks))
    body = head + table + b''.join(comp)
    if not pad:
        return body
    return body + b'\0' * (-len(body) % PAD)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    cmd, src, dst = argv[0], argv[1], argv[2]
    data = open(src, 'rb').read()
    if cmd == 'unpack':
        open(dst, 'wb').write(unpack(data))
    elif cmd == 'pack':
        level = int(argv[argv.index('--level') + 1]) if '--level' in argv else 9
        open(dst, 'wb').write(pack(data, level))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
