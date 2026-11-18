"""GFx/SWF 태그 목록·글꼴 정보 보기(조사용).

사용: python -I tools/swf_tags.py <파일.gfx>
"""
import collections
import struct
import sys


def tags(d):
    nbits = d[8] >> 3
    rect_bytes = (5 + nbits * 4 + 7) // 8
    p = 8 + rect_bytes + 4
    while p < len(d):
        code_len = struct.unpack_from('<H', d, p)[0]
        code, ln = code_len >> 6, code_len & 0x3F
        p += 2
        if ln == 0x3F:
            ln = struct.unpack_from('<I', d, p)[0]
            p += 4
        yield code, p, ln
        p += ln
        if code == 0:
            break


def font_info(body, code):
    fid = struct.unpack_from('<H', body, 0)[0]
    flags = body[2]
    lang = body[3]
    nlen = body[4]
    name = body[5:5 + nlen].decode('utf-8', 'replace')
    nglyph = struct.unpack_from('<H', body, 5 + nlen)[0]
    return fid, name, nglyph, flags


def main(path):
    d = open(path, 'rb').read()
    print('sig', d[:3], 'ver', d[3], 'len', struct.unpack_from('<I', d, 4)[0])
    cnt = collections.Counter()
    size = collections.Counter()
    for code, p, ln in tags(d):
        cnt[code] += 1
        size[code] += ln
        if code in (48, 75):
            print('DefineFont%d' % (2 if code == 48 else 3), ascii(font_info(d[p:p + ln], code)), 'bytes', ln)
        if code == 1005:  # DefineCompactedFont
            fid = struct.unpack_from('<H', d, p)[0]
            print('CompactedFont id', fid, 'bytes', ln)
        if code == 88:
            fid = struct.unpack_from('<H', d, p)[0]
            print('FontName', fid, d[p + 2:p + ln].split(b'\0')[0])
        if code in (56, 1003):  # ExportAssets / GFx 표
            pass
    for c, n in sorted(cnt.items()):
        print('tag', c, 'count', n, 'bytes', size[c])


if __name__ == '__main__':
    main(sys.argv[1])


def rebuild(d, replace):
    """replace: {태그 본문 위치(p): 새 본문}. 원래 긴 머리였던 태그는 긴 머리를 유지한다.
    파일 길이(4~8바이트)를 고치고, 선언 길이 뒤에 붙은 바이트는 그대로 둔다."""
    nbits = d[8] >> 3
    rect_bytes = (5 + nbits * 4 + 7) // 8
    start = 8 + rect_bytes + 4
    declared = struct.unpack_from('<I', d, 4)[0]
    out = [d[:start]]
    prev = start
    for code, p, ln in tags(d):
        was_long = (p - prev) == 6
        body = replace.get(p, d[p:p + ln])
        n = len(body)
        if was_long or n >= 0x3F:
            out.append(struct.pack('<HI', (code << 6) | 0x3F, n))
        else:
            out.append(struct.pack('<H', (code << 6) | n))
        out.append(body)
        prev = p + ln
    res = bytearray(b''.join(out))
    struct.pack_into('<I', res, 4, len(res))
    return bytes(res) + d[declared:]
