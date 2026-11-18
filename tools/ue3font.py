"""UE3 Font 오브젝트(자막 폰트) 해석·다시 쓰기.

익스포트 = NetIndex(u32) + 프로퍼티들 + None + 네이티브 CharRemap(TMap<u16,u16>: i32 수, (u16 키, u16 값)…)
프로퍼티 태그(빅엔디언): 이름(u32 idx, u32 num), 형(u32 idx, u32 num), 크기 i32, 배열 번호 i32, 값
  BoolProperty 는 값 1바이트(크기 0), ByteProperty 는 enum 이름(8) + 값
  Characters(ArrayProperty) = i32 개수 + FontCharacter × n (StartU, StartV, USize, VSize i32, TextureIndex u8, VerticalOffset i32 = 21바이트)
"""
import struct


class Prop:
    def __init__(self, name, typ, size, idx, raw, extra=b''):
        self.name, self.typ, self.size, self.idx, self.raw, self.extra = name, typ, size, idx, raw, extra


def parse_font(b, names):
    p = 4
    net = b[:4]
    props = []
    while True:
        ni, nn = struct.unpack_from('>ii', b, p)
        name = names[ni]
        p += 8
        if name == 'None':
            break
        ti, tn, size, aidx = struct.unpack_from('>iiii', b, p)
        typ = names[ti]
        p += 16
        extra = b''
        if typ == 'BoolProperty':
            raw = b[p:p + 1]
            p += 1
        elif typ == 'ByteProperty':
            extra = b[p:p + 8]
            p += 8
            raw = b[p:p + size]
            p += size
        elif typ == 'StructProperty':
            extra = b[p:p + 8]
            p += 8
            raw = b[p:p + size]
            p += size
        else:
            raw = b[p:p + size]
            p += size
        props.append(Prop(name, typ, size, aidx, raw, extra))
    native = b[p:]
    return net, props, native


def chars_of(raw):
    n = struct.unpack_from('>i', raw, 0)[0]
    out = []
    for i in range(n):
        su, sv, us, vs, ti, vo = struct.unpack_from('>iiiiBi', raw, 4 + 21 * i)
        out.append([su, sv, us, vs, ti, vo])
    return out


def chars_raw(chars):
    return struct.pack('>i', len(chars)) + b''.join(struct.pack('>iiiiBi', *c) for c in chars)


def remap_of(native):
    n = struct.unpack_from('>i', native, 0)[0]
    pairs = [struct.unpack_from('>HH', native, 4 + 4 * i) for i in range(n)]
    return pairs, native[4 + 4 * n:]


def remap_raw(pairs, rest):
    return struct.pack('>i', len(pairs)) + b''.join(struct.pack('>HH', k, v) for k, v in pairs) + rest


def build_font(net, props, native, names_idx):
    out = [net]
    for pr in props:
        out.append(struct.pack('>ii', names_idx[pr.name], 0))
        raw = pr.raw
        size = len(raw) if pr.typ != 'BoolProperty' else 0
        out.append(struct.pack('>iiii', names_idx[pr.typ], 0, size, pr.idx))
        out.append(pr.extra + raw)
    out.append(struct.pack('>ii', names_idx['None'], 0))
    out.append(native)
    return b''.join(out)
