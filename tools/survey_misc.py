"""패키지 밖 파일 조사: rpx, .sav, meta.xml, Manual.bfma(SARC 목록), pck(AKPK 언어표), Movies 이름, 사전, 기타 글 파일.
출력: work/survey/misc_report.json
"""
import glob
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rpx_unpack  # noqa: E402
import scan_jp  # noqa: E402

ROOT = os.path.dirname(HERE)
G = os.path.join(ROOT, 'Devils Third [Game] [0005000010138f00]')
C = os.path.join(G, 'content', 'DevilsThirdGame')
SJIS = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]){4,}')


def sjis_strings(b):
    out = []
    for m in SJIS.finditer(b):
        try:
            s = m.group(0).decode('cp932')
        except UnicodeDecodeError:
            continue
        if re.search('[぀-ヿ]', s):
            out.append(s)
    return out


def sarc_list(b):
    assert b[:4] == b'SARC'
    bom = b[6:8]
    e = '>' if bom == b'\xfe\xff' else '<'
    hdr = struct.unpack_from(e + 'H', b, 4)[0]
    data_off = struct.unpack_from(e + 'I', b, 0xC)[0]
    p = hdr
    assert b[p:p + 4] == b'SFAT'
    n = struct.unpack_from(e + 'H', b, p + 6)[0]
    ents = []
    for i in range(n):
        h, attr, s, en = struct.unpack_from(e + 'IIII', b, p + 12 + 16 * i)
        ents.append((attr, s, en))
    q = p + 12 + 16 * n
    assert b[q:q + 4] == b'SFNT'
    names_base = q + 8
    out = []
    for attr, s, en in ents:
        if attr & 0x01000000:
            off = (attr & 0xFFFF) * 4
            nm = b[names_base + off:b.index(b'\0', names_base + off)].decode('utf-8', 'replace')
        else:
            nm = '?'
        out.append((nm, en - s, b[data_off + s:data_off + s + 4].hex()))
    return out, data_off, ents


def main():
    rep = {}
    # rpx
    rp = os.path.join(G, 'code', 'DevilsThirdGame-WiiU-Shipping.rpx')
    rjp = []
    for i, typ, flags, addr, raw in rpx_unpack.sections(open(rp, 'rb').read()):
        if typ == 1 and raw:
            for k, s in scan_jp.scan_bytes(raw):
                rjp.append((hex(addr), k, s))
            for s in sjis_strings(raw):
                rjp.append((hex(addr), 'sjis', s))
    rep['rpx_jp'] = rjp
    # sav
    sav = []
    for p in glob.glob(os.path.join(glob.escape(C), 'Checkpoints', '*.sav')):
        b = open(p, 'rb').read()
        hits = scan_jp.scan_bytes(b) + [('sjis', s) for s in sjis_strings(b)]
        if hits:
            sav.append((os.path.basename(p), hits[:5]))
    rep['sav_jp'] = sav
    rep['sav_head'] = open(sorted(glob.glob(os.path.join(glob.escape(C), 'Checkpoints', '*.sav')))[0], 'rb').read(300).decode('utf-8', 'replace')
    # meta.xml
    mx = open(os.path.join(G, 'meta', 'meta.xml'), encoding='utf-8').read()
    rep['meta_names'] = re.findall(r'<((?:long|short)name_\w+|publisher_\w+)[^>]*>([^<]*)<', mx)
    # Manual.bfma
    mb = open(os.path.join(G, 'meta', 'Manual.bfma'), 'rb').read()
    try:
        rep['manual'] = sarc_list(mb)[0]
    except Exception as e:  # noqa: BLE001
        rep['manual'] = repr(e)
    # pck 언어표
    pk = {}
    for p in glob.glob(os.path.join(glob.escape(C), 'CookedWiiU', '*.pck')):
        b = open(p, 'rb').read(0x2000)
        strs = re.findall(rb'(?:[a-z()]\x00){4,}', b)
        pk[os.path.basename(p)] = [s.decode('utf-16-le') for s in strs][:12]
    rep['pck_langs'] = pk
    # 영상 이름
    rep['movies'] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(glob.escape(C), 'Movies', '*.bk2')))
    # 사전
    rep['dictionaries'] = sorted(os.path.relpath(p, C) for p in glob.glob(os.path.join(glob.escape(C), 'Dictionaries', '**', '*'), recursive=True))
    json.dump(rep, open(os.path.join(ROOT, 'work', 'survey', 'misc_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
