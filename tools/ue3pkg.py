"""UE3 패키지(.xxx, 빅엔디언, 버전 868 / 라이선시 1) 풀기·표 읽기.

두 가지 형식이 섞여 있다.
  1) 통째 압축: .uncompressed_size 짝이 있는 파일. tools/ue3full.py 로 푼다.
  2) 일반 패키지: 머리(이름·임포트·익스포트 표)는 그대로, 몸통은 압축 청크 표에 따라 zlib 블록.
     머리 0x75 근처: CompressionFlags(1=zlib), 청크 수, (풀린 위치, 풀린 크기, 압축 위치, 압축 크기)×n
     각 청크 = ue3full 과 같은 블록 형식(9E2A83C1, 0x20000, 합계, 원래 크기, 표, zlib…)

머리 오프셋(실측):
  0x00 tag 9E2A83C1, 0x04 버전(0x00010364), 0x08 머리 크기, 0x0C FString 폴더("None")
  그 뒤 u32 PackageFlags, NameCount, NameOffset, ExportCount, ExportOffset,
  ImportCount, ImportOffset, DependsOffset, …

사용:
  python -I tools/ue3pkg.py unpack <입력.xxx> <출력.upk>      (통째 압축도 알아서 처리)
  python -I tools/ue3pkg.py list <입력.xxx 또는 .upk> [출력.json]
"""
import json
import struct
import sys
import zlib

sys.path.insert(0, __file__.rsplit('\\', 1)[0].rsplit('/', 1)[0])
import ue3full  # noqa: E402

TAG = 0x9E2A83C1


def be(fmt, b, o):
    return struct.unpack_from('>' + fmt, b, o)


class Pkg:
    def __init__(self, data):
        self.raw = data
        self.p = 0
        tag, ver, self.header_size = be('3I', data, 0)
        assert tag == TAG, hex(tag)
        self.p = 12
        self.folder = self.fstr()
        (self.flags, self.name_count, self.name_off, self.exp_count, self.exp_off,
         self.imp_count, self.imp_off, self.depends_off) = be('8I', data, self.p)
        self.p += 32
        # 청크 표 위치를 찾는다: CompressionFlags 다음에 청크 수, 첫 청크의 풀린 위치=NameOffset
        self.chunks = []
        self.comp_flags = 0
        key = struct.pack('>I', self.name_off)
        i = data.find(key, self.p, self.header_size if self.header_size < len(data) else 0x400)
        while i != -1:
            cnt = be('I', data, i - 4)[0]
            cf = be('I', data, i - 8)[0]
            if 0 < cnt < 4096 and cf in (1, 2, 4):
                chunks = [be('4I', data, i + 16 * k) for k in range(cnt)]
                if all(c[2] + c[3] <= len(data) for c in chunks):
                    self.chunks, self.comp_flags, self.chunk_table_off = chunks, cf, i - 8
                    break
            i = data.find(key, i + 1, 0x400)

    def fstr(self):
        n = be('i', self.raw, self.p)[0]
        self.p += 4
        if n >= 0:
            s = self.raw[self.p:self.p + n].rstrip(b'\0').decode('latin-1')
            self.p += n
        else:
            s = self.raw[self.p:self.p - n * 2].decode('utf-16-be', 'replace').rstrip('\0')
            self.p += -n * 2
        return s

    def unpacked(self):
        if not self.chunks:
            return self.raw
        size = max(u + s for u, s, _, _ in self.chunks)
        out = bytearray(size)
        out[:self.chunks[0][0]] = self.raw[:self.chunks[0][0]]
        for uo, us, co, cs in self.chunks:
            block = ue3full.unpack(self.raw[co:co + cs])
            assert len(block) == us
            out[uo:uo + us] = block
        return bytes(out)


def tables(data):
    pk = Pkg(data)
    body = pk.unpacked()
    pk.raw = body
    names = []
    pk.p = pk.name_off
    for _ in range(pk.name_count):
        names.append(pk.fstr())
        pk.p += 8
    imps = []
    o = pk.imp_off
    for _ in range(pk.imp_count):
        cp, cpn, cn, cnn, outer, on, onn = be('7i', body, o)
        imps.append({'class': names[cn], 'name': names[on], 'outer': outer})
        o += 28
    exps = []
    o = pk.exp_off
    for _ in range(pk.exp_count):
        cls, sup, outer, nm, nnum, arch = be('6i', body, o)
        flags = be('Q', body, o + 24)[0]
        ssize, soff, eflags, netn = be('4i', body, o + 32)
        o += 48 + netn * 4 + 16 + 4
        cname = 'Class' if cls == 0 else (imps[-cls - 1]['name'] if cls < 0 else names[0])
        exps.append({'class': cname, 'name': names[nm] + ('_%d' % (nnum - 1) if nnum else ''),
                     'outer': outer, 'size': ssize, 'offset': soff})
    return pk, body, names, imps, exps


def main(argv):
    cmd, src = argv[0], argv[1]
    data = open(src, 'rb').read()
    if be('I', data, 4)[0] == 0x20000:
        data = ue3full.unpack(data)
    if cmd == 'unpack':
        open(argv[2], 'wb').write(Pkg(data).unpacked())
    elif cmd == 'list':
        pk, body, names, imps, exps = tables(data)
        info = {'chunks': len(pk.chunks), 'names': len(names), 'imports': imps, 'exports': exps}
        if len(argv) > 2:
            json.dump(info, open(argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        else:
            for e in exps:
                print(e['class'], e['name'], e['size'])


if __name__ == '__main__':
    main(sys.argv[1:])


def export_entries(body, pk):
    """익스포트 표 항목마다 (표 안 위치, 크기, 데이터 위치)."""
    out = []
    o = pk.exp_off
    for _ in range(pk.exp_count):
        ssize, soff = be('ii', body, o + 32)
        netn = be('i', body, o + 44)[0]
        out.append((o, ssize, soff))
        o += 48 + netn * 4 + 16 + 4
    return out


def fix_bulk_offsets(data, old_base, new_base):
    """벌크 데이터 머리(flags, 개수, 디스크 크기, OffsetInFile)의 OffsetInFile 은 파일 안 절대 위치(바로 뒤 바이트).
    익스포트가 옮겨지면 이 값을 새 위치로 고친다. 조건: u32 값 == old_base + j + 4 이고 앞 두 값이 같음(개수 == 크기)."""
    import numpy as np
    a = np.frombuffer(data, np.uint8)
    if len(a) < 16:
        return data
    v = (a[:-3].astype(np.uint32) << 24) | (a[1:-2].astype(np.uint32) << 16) | (a[2:-1].astype(np.uint32) << 8) | a[3:]
    j = np.arange(len(v), dtype=np.int64)
    hit = np.nonzero(v.astype(np.int64) == old_base + j + 4)[0]
    out = bytearray(data)
    for k in hit:
        if k >= 8 and data[k - 8:k - 4] == data[k - 4:k]:
            struct.pack_into('>I', out, int(k), new_base + int(k) + 4)
    return bytes(out)


def repack(raw, replace):
    """일반 패키지 다시 묶기(압축 청크 있음/없음 둘 다). replace: {익스포트 번호: 새 데이터}.
    익스포트 데이터 크기가 바뀌면 뒤쪽 익스포트 위치·청크 경계를 밀고, 청크를 zlib 6으로 다시 압축한다.
    파일 머리(청크 표 포함)는 원본을 쓰고 청크 표만 고친다. 파일 끝은 0x8000 경계로 채운다."""
    pk = Pkg(raw)
    body = bytearray(pk.unpacked())
    ents = export_entries(body, pk)
    order = sorted(range(len(ents)), key=lambda i: ents[i][2])
    first = min(e[2] for e in ents)
    new = bytearray(body[:first])
    shifts = []  # (원래 위치, 누적 차이) — 이 위치 이후는 차이만큼 밀림
    delta = 0
    cur = first
    newpos = {}
    for i in order:
        _, ssize, soff = ents[i]
        assert soff >= cur, '익스포트가 겹침'
        new += body[cur:soff]
        data = replace.get(i, bytes(body[soff:soff + ssize]))
        if len(new) != soff:
            data = fix_bulk_offsets(data, soff, len(new))
        newpos[i] = (len(new), len(data))
        new += data
        cur = soff + ssize
        if len(data) != ssize:
            delta += len(data) - ssize
            shifts.append((cur, delta))
    new += body[cur:]
    for i, (o, _, _) in enumerate(ents):
        p, s = newpos[i]
        struct.pack_into('>ii', new, o + 32, s, p)

    def moved(x):
        d = 0
        for at, dd in shifts:
            if x >= at:
                d = dd
        return x + d
    if not pk.chunks:
        # 청크 없는 패키지(통째 압축 패키지의 속 등): 다시 묶은 몸통 그대로 돌려줌(채움 없음)
        return bytes(new)
    # 청크 경계: 시작 위치는 밀린 위치, 크기는 다음 시작까지
    starts = [moved(c[0]) for c in pk.chunks]
    ends = starts[1:] + [len(new)]
    hdr = bytearray(raw[:pk.chunks[0][2]])
    pos = len(hdr)
    blobs = []
    for k, (s, e) in enumerate(zip(starts, ends)):
        blk = ue3full.pack(bytes(new[s:e]), 6, pad=False)
        struct.pack_into('>4I', hdr, pk.chunk_table_off + 8 + 16 * k, s, e - s, pos, len(blk))
        blobs.append(blk)
        pos += len(blk)
    out = bytes(hdr) + b''.join(blobs)
    return out + b'\0' * (-len(out) % 0x8000)


def set_array_prop(exp, names, prop_name, payload):
    """익스포트 데이터에서 바이트 배열 프로퍼티(ArrayProperty, 원소 1바이트)를 통째로 바꾼다."""
    ni = names.index(prop_name)
    key = struct.pack('>ii', ni, 0) + struct.pack('>ii', names.index('ArrayProperty'), 0)
    i = exp.find(key)
    assert i != -1, prop_name
    size, aidx, count = be('iii', exp, i + 16)
    assert size == count + 4
    start = i + 28
    return exp[:i + 16] + struct.pack('>iii', len(payload) + 4, aidx, len(payload)) + payload + exp[start + count:]


def get_array_prop(exp, names, prop_name):
    ni = names.index(prop_name)
    key = struct.pack('>ii', ni, 0) + struct.pack('>ii', names.index('ArrayProperty'), 0)
    i = exp.find(key)
    size, aidx, count = be('iii', exp, i + 16)
    return exp[i + 28:i + 28 + count]
