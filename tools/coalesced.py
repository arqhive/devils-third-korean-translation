"""Coalesced_XXX.bin(UE3 설정·언어 문자열 묶음) 풀기·묶기.

암호: AES-256 ECB, 키는 rpx .rodata 0xA8(=0x100000A8)에 있는 32바이트 문자열. 끝은 0으로 16배수 채움.
평문(정수는 빅엔디언):
  i32 파일 수
  파일마다: FString 이름, i32 구역 수
    구역마다: FString 이름, i32 키 수
      키마다: FString 키, FString 값
FString: i32 길이 n. n>0 이면 ASCII n바이트(끝 0 포함), n<0 이면 UTF-16LE -n글자(끝 0 포함), 0이면 빈 문자열.

사용:
  python -I tools/coalesced.py dump <Coalesced.bin> <출력.json>
  python -I tools/coalesced.py build <입력.json> <출력.bin>
  python -I tools/coalesced.py roundtrip <Coalesced.bin>
"""
import json
import struct
import sys

from Crypto.Cipher import AES

KEY = b'D3vi15-Th3rd_0n1in3@A35*k3Y!2ol3'


def decrypt(data):
    return AES.new(KEY, AES.MODE_ECB).decrypt(data)


def encrypt(plain):
    plain += b'\0' * (-len(plain) % 16)
    return AES.new(KEY, AES.MODE_ECB).encrypt(plain)


class Reader:
    def __init__(self, b):
        self.b, self.p = b, 0

    def i32(self):
        v = struct.unpack_from('>i', self.b, self.p)[0]
        self.p += 4
        return v

    def fstr(self):
        n = self.i32()
        if n == 0:
            return {'s': '', 'w': False, 'z': False}
        if n > 0:
            raw = self.b[self.p:self.p + n]
            self.p += n
            return {'s': raw[:-1].decode('latin-1'), 'w': False}
        n = -n
        raw = self.b[self.p:self.p + n * 2]
        self.p += n * 2
        return {'s': raw[:-2].decode('utf-16-le'), 'w': True}


def parse(plain):
    r = Reader(plain)
    files = []
    for _ in range(r.i32()):
        name = r.fstr()
        secs = []
        for _ in range(r.i32()):
            sname = r.fstr()
            keys = []
            for _ in range(r.i32()):
                k = r.fstr()
                v = r.fstr()
                keys.append([k, v])
            secs.append([sname, keys])
        files.append([name, secs])
    return files, r.p


def wstr(f):
    s = f['s']
    if s == '' and f.get('z') is False:
        return struct.pack('>i', 0)
    if f['w']:
        raw = s.encode('utf-16-le') + b'\0\0'
        return struct.pack('>i', -(len(raw) // 2)) + raw
    raw = s.encode('latin-1') + b'\0'
    return struct.pack('>i', len(raw)) + raw


def serialize(files):
    out = [struct.pack('>i', len(files))]
    for name, secs in files:
        out += [wstr(name), struct.pack('>i', len(secs))]
        for sname, keys in secs:
            out += [wstr(sname), struct.pack('>i', len(keys))]
            for k, v in keys:
                out += [wstr(k), wstr(v)]
    return b''.join(out)


def main(argv):
    cmd = argv[0]
    if cmd == 'dump':
        plain = decrypt(open(argv[1], 'rb').read())
        files, end = parse(plain)
        assert not plain[end:].strip(b'\0'), '끝에 남는 데이터'
        json.dump(files, open(argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    elif cmd == 'build':
        files = json.load(open(argv[1], encoding='utf-8'))
        open(argv[2], 'wb').write(encrypt(serialize(files)))
    elif cmd == 'roundtrip':
        data = open(argv[1], 'rb').read()
        files, _ = parse(decrypt(data))
        re = encrypt(serialize(files))
        print('SAME' if re == data else 'DIFF %d vs %d' % (len(re), len(data)))
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
