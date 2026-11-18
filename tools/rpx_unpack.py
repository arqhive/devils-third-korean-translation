"""RPX 섹션 압축 풀기(조사용). 압축 섹션(flag 0x08000000)은 앞 4바이트=원래 크기, 뒤는 zlib.

사용: python -I tools/rpx_unpack.py <입력.rpx> <출력 폴더>
섹션마다 <번호>_<종류>.bin 으로 저장한다.
"""
import os
import struct
import sys
import zlib

SHF_RPL_ZLIB = 0x08000000


def sections(data):
    shoff = struct.unpack_from('>I', data, 0x20)[0]
    shentsize, shnum = struct.unpack_from('>HH', data, 0x2E)
    for i in range(shnum):
        name, typ, flags, addr, off, size = struct.unpack_from('>6I', data, shoff + i * shentsize)
        raw = data[off:off + size]
        if flags & SHF_RPL_ZLIB and size:
            usz = struct.unpack_from('>I', raw, 0)[0]
            raw = zlib.decompress(raw[4:])
            assert len(raw) == usz
        yield i, typ, flags, addr, raw


def main(src, out):
    data = open(src, 'rb').read()
    os.makedirs(out, exist_ok=True)
    for i, typ, flags, addr, raw in sections(data):
        open(os.path.join(out, '%02d_t%X_a%08X.bin' % (i, typ, addr)), 'wb').write(raw)
        print(i, hex(typ), hex(flags), hex(addr), len(raw))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
