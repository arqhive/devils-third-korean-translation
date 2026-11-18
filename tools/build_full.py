"""8단계 본 빌드.

넣는 것
  1) Coalesced_JPN.bin: work/translation/ko.json 번역(솔로 3,285줄). 바꾸는 줄은 원문이 text_jpn.json 과 같은지 확인
  2) UI_Fonts.xxx: fonts_en(GFx) 의 '国' 있는 글꼴마다 한글(번역에 쓰인 글자) 추가
       SB 어그로 — Mechanical-NewRodinUB 계열 = B, 나머지 = M / 원래 진행 폭(natural, track 0), 띄어쓰기도 어그로 폭
  3) VGSBase_LOC_JPN.xxx: 자막 폰트 SubtitleFont 에 한글 추가(subfont.inject_natural, 어그로 M 원래 폭),
       띄어쓰기·“”‘’ 도 어그로로 다시 그림. 칸 번호는 번역 뒤 안 쓰는 한자 칸을 물려받음
  4) WiiUTOC*.txt: 바뀐 파일 크기 반영
출력: work/build/full/sdcafiine/0005000010138F00/DevilsThirdKR/content/DevilsThirdGame/…
      work/build/full/build_log.txt, preview_*.png

사용: python -I -X utf8 tools/build_full.py
"""
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_test as bt  # noqa: E402
import coalesced  # noqa: E402
import gfxfont  # noqa: E402
import hangul_gfx  # noqa: E402
import subfont  # noqa: E402
import swf_tags  # noqa: E402
import ue3font  # noqa: E402
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402

ROOT = bt.ROOT
COOKED = bt.COOKED
SUBTITLE_SCALE = 1.0  # 원본값. 11/18 1.3(줄 간격 39)으로 Cemu 시험 → 자막 크기 그대로(이 ini 값은 효과 없음) → 되돌림
SUBTITLE_SET = {} if SUBTITLE_SCALE == 1.0 else {
    'SubtitleFontScaleX': '%.2f' % SUBTITLE_SCALE,
    'SubtitleFontScaleY': '%.2f' % SUBTITLE_SCALE,
    'SubtitleOffsetLineY': '%.1f' % (30.0 * SUBTITLE_SCALE),  # 줄 간격(원본 30.0)도 같은 비율
}
GFX_REDRAW = '“”‘’'  # 메뉴(GFx) 글꼴에서 어그로로 다시 그릴 부호(일본어 전각 폭 → 어그로 폭)
PUNCT_LEFT_PAD = 2  # 자막 「!」「?」 앞 빈칸(px), 11/18 사용자 2px 선택
# 자막 「…」 앞 빈칸(px). 원래 일본어 글꼴 칸(폭 20, 점 사이 3~4px, 왼쪽 여백 0·오른쪽 1)이라
# 「……」 경계에서 점이 1px로 붙음(11/18 사용자) → 3px 넣으면 경계 4px = 칸 안 점 간격과 같음(사용자 「3px 넣어」)
ELLIPSIS_LEFT_PAD = 3
SKIP_REUSE = True  # SkipFont: 칸 덧붙이기 대신 키·스·ッ·プ 칸 다시 쓰기(11/18 「IKAE」 깨짐 대조판)
OUT = os.path.join(ROOT, 'work', 'build', 'full')
# 한글 글꼴(11/18 사용자 「넥슨 워헤이븐으로 바꾸자, 크기가 들쑥날쑥」). 'aggro' 로 되돌릴 수 있음
FONT_SET = 'warhaven'
if FONT_SET == 'warhaven':
    # 넥슨 워헤이븐(brand.nexon.com, 임베딩·상업 허용, 수정 금지 → 꼭지 누르기 같은 모양 수정 안 함)
    TTF_M = os.path.join(HERE, 'fonts', 'NEXON_Warhaven_Regular.ttf')
    TTF_B = os.path.join(HERE, 'fonts', 'NEXON_Warhaven_Bold.ttf')
    GFX_CAP = {'M': None, 'B': None}
    TTF_SUB = TTF_B  # 자막·스킵 글꼴은 굵게(11/18 사용자 「굵게」), 메뉴 M 자리는 보통
else:
    TTF_M = os.path.join(HERE, 'fonts', 'SB_Aggro_M.ttf')
    TTF_B = os.path.join(HERE, 'fonts', 'SB_Aggro_B.ttf')
    # GFx 글꼴: ㅊ·ㅎ 꼭지 누르기 (TTF 단위: 이 높이 위만 눌러서, 위 끝을 이 값에) — 위 끝 735(B 740)인 속·옥·슬 은 실기·Cemu 에서 정상
    GFX_CAP = {'M': (640, 735), 'B': (645, 740)}  # 사용자 결정(11/06 「꼭지 눌러 쓸게」)
    TTF_SUB = TTF_M
REDRAW = '“”‘’'
# 자막 한글을 세로 힌팅(tools/vhint.py)으로 그림(11/18 사용자 「포로 ㅗ 획 기준선 어긋남」·「ㄹ 도 ㅍ 이랑 정렬 안 됨」)
# False 면 이전처럼 Pillow 로 바로 그림
SUB_HINT = True
# 보이지 않는 점으로 크기 상자 맞추기: Cemu 에서 효과 없음(GFx 는 실제 윤곽 모서리를 픽셀에 맞춤) → 끔
GFX_BOX = {'M': None, 'B': None}
# fonts_en 이 $SentenceFont 이름으로 내보내는 실제 글꼴. 글꼴 묶음을 안 쓰는 무비(TVWarning 등)는
# fonts_en.swf 에서 직접 가져온 이 글꼴만 가지므로, 연결표도 이 이름이어야 본체 글꼴로 안 넘어감
# 11/06: NewCez 로 바꿨던 건 「GamePad 알림 = TVWarning」 가설 때문이었는데 틀렸음(실제는 실행 파일이 자막 폰트로 그림).
# 옵션 화면 글자 빠짐의 진짜 원인은 hangul_gfx 의 변수 이름 겹침 버그(엉뚱한 윤곽)였고 연결과는 무관. 실기에서 확인된 OptiB 로 둠
SENTENCE_FONT = 'OptiB-NewRodinB85-NTLGDB002'
# TVWarning 무비에 글꼴 직접 넣기: 컨트롤러 알림 네모의 원인이 아니었음(실제 원인은 VGSBase_LOC_INT 자막 폰트) → 확인 전까지 끔
EMBED_TV_FONT = False

# build_test 의 쓰기·목차 함수가 이 빌드 폴더를 쓰게 함
bt.OUT = OUT
bt.SD = os.path.join(OUT, 'sdcafiine', '0005000010138F00', 'DevilsThirdKR', 'content')
log, write = bt.log, bt.write


def build_coalesced(ko, src):
    data = open(os.path.join(COOKED, 'Coalesced_JPN.bin'), 'rb').read()
    files, _ = coalesced.parse(coalesced.decrypt(data))
    hit = {}
    for name, secs in files:
        fname = name['s'].split('\\')[-1].rsplit('.', 1)[0]
        for sname, keys in secs:
            for k, v in keys:
                key = '%s|%s|%s' % (fname, sname['s'], k['s'])
                if key in ko:
                    if v['s'] != src[key]:
                        raise SystemExit('원문이 다름: %s' % key)
                    v['s'] = ko[key]
                    v['w'] = True
                    v.pop('z', None)
                    hit[key] = hit.get(key, 0) + 1
    # 논리 글꼴 $SentenceFont(TT_TsukuGo-B)는 fonts_en 에 없어 본체 글꼴로 그려짐(한글 없음) → OptiB 로 연결
    font_set = 0
    for name, secs in files:
        if name['s'].lower().endswith('\\gfxui.jpn'):
            for sname, keys in secs:
                if sname['s'] == 'Fonts':
                    for k, v in keys:
                        if k['s'] == 'SentenceFont':
                            log('GFxUI SentenceFont', v['s'], '->', SENTENCE_FONT)
                            v['s'] = SENTENCE_FONT
                            font_set += 1
    if font_set != 1:
        raise SystemExit('GFxUI.jpn SentenceFont 를 못 찾음(%d)' % font_set)
    # 자막 크기(11/18 사용자 「너무 작음」): D3Engine 자막 배율·줄 간격을 같은 비율로 키움(5개 ini 모두)
    sub_set = 0
    for name, secs in files:
        for sname, keys in secs:
            if sname['s'] == 'DevilsThirdGame.D3Engine':
                for k, v in keys:
                    if k['s'] in SUBTITLE_SET:
                        v['s'] = SUBTITLE_SET[k['s']]
                        sub_set += 1
    log('자막 크기 설정', SUBTITLE_SET, '바꾼 칸', sub_set)
    if SUBTITLE_SET and sub_set != 5 * len(SUBTITLE_SET):
        raise SystemExit('자막 크기 설정 칸 수가 다름(%d)' % sub_set)
    miss = set(ko) - set(hit)
    if miss:
        raise SystemExit('못 찾은 키 %d: %s' % (len(miss), sorted(miss)[:5]))
    dup = {k: n for k, n in hit.items() if n > 1}
    log('coalesced 바꾼 키', len(hit), '여러 번 나온 키', len(dup), sorted(dup)[:10])
    return coalesced.encrypt(coalesced.serialize(files)), files


def build_ui_fonts(chars, keep, skip_chars):
    raw = open(os.path.join(COOKED, 'UI_Fonts.xxx'), 'rb').read()
    pk, body, names, imps, exps = ue3pkg.tables(raw)
    k = [i for i, e in enumerate(exps) if e['class'] == 'SwfMovie'][0]
    e = exps[k]
    exp = body[e['offset']:e['offset'] + e['size']]
    g = ue3pkg.get_array_prop(exp, names, 'RawData')
    srcs = {'M': hangul_gfx.HangulSource(TTF_M), 'B': hangul_gfx.HangulSource(TTF_B)}
    rep, previews = {}, []
    for code, p, ln in swf_tags.tags(g):
        if code != 75:
            continue
        f = gfxfont.Font3(g[p:p + ln])
        fname = f.name.rstrip(b'\0').decode('utf-8', 'replace')
        w = 'B' if 'NewRodinUB' in fname else 'M'
        n = hangul_gfx.add_to_font(f, srcs[w], chars, mode='natural', track=0.0, space='ttf', cap=GFX_CAP[w], box=GFX_BOX[w])
        log('gfx font', f.id, fname, w, 'added', n, 'glyphs', len(f.codes))
        if n:
            if n != len(chars):
                raise SystemExit('글꼴 %s: 한글 %d/%d 만 들어감' % (fname, n, len(chars)))
            # 11/18 사용자 「‘“ 사이에 엄청난 공백」: 일본어 글꼴의 “”‘’ 는 진행 폭 1em(한글 한 글자 폭)이라 벌어짐
            # → 어그로 글리프·폭(“ 0.51em, ‘ 0.315em)으로 바꿈(자막 글꼴은 이미 어그로)
            q = [c for c in GFX_REDRAW if ord(c) in f.codes]
            if q:
                hangul_gfx.add_to_font(f, srcs[w], q, mode='natural', track=0.0)
                log('gfx font', fname, '부호 다시 그림', ''.join(q))
            rep[p] = f.serialize()
            previews.append(f)
    g2 = swf_tags.rebuild(g, rep)
    exp2 = ue3pkg.set_array_prop(exp, names, 'RawData', g2)
    rep2, _, _, _ = font_replacements((pk, body, names, imps, exps), chars, keep, skip_chars, 'UI_Fonts')
    assert k not in rep2
    rep2[k] = exp2
    return ue3pkg.repack(raw, rep2), previews, g, g2


def subset_font(swf, font_name, chars, new_id):
    """swf 안 DefineFont3(font_name) 에서 chars 글자만 남긴 새 글꼴 태그 본문(글꼴 번호 new_id, 커닝 표 비움)."""
    for code, p, ln in swf_tags.tags(swf):
        if code == 75:
            f = gfxfont.Font3(swf[p:p + ln])
            if f.name.rstrip(b'\0').decode('utf-8', 'replace') == font_name:
                keep = [i for i, c in enumerate(f.codes) if chr(c) in chars]
                f.id = new_id
                f.codes = [f.codes[i] for i in keep]
                f.shapes = [f.shapes[i] for i in keep]
                if f.layout:
                    f.layout['adv'] = [f.layout['adv'][i] for i in keep]
                    f.layout['rects'] = [f.layout['rects'][i] for i in keep]
                    f.layout['kc'] = 0
                    f.layout['kern'] = b''
                return f.serialize(), len(keep)
    raise SystemExit('글꼴 없음: %s' % font_name)


def embed_font_for_import(movie, font_body):
    """무비의 ImportAssets2 로 fonts_en 에서 가져오던 글꼴 1개를 같은 번호의 DefineFont3 로 바꿔 넣는다.
    (TVWarning: 글꼴 묶음 없이 가져오기가 실패해 본체 글꼴로 넘어가 한글이 네모)"""
    nbits = movie[8] >> 3
    start = 8 + (5 + nbits * 4 + 7) // 8 + 4
    out = [movie[:start]]
    done = 0
    prev = start
    for code, p, ln in swf_tags.tags(movie):
        body = movie[p:p + ln]
        was_long = (p - prev) == 6
        prev = p + ln
        if code == 71:
            url_end = body.index(b'\0')
            assert body[:url_end].endswith(b'fonts_en.swf'), body[:url_end]
            q = url_end + 1 + 2  # 플래그 2바이트
            n = struct.unpack_from('<H', body, q)[0]
            assert n == 1, n
            fid = struct.unpack_from('<H', body, q + 2)[0]
            assert struct.unpack_from('<H', font_body, 0)[0] == fid
            code, body = 75, font_body
            done += 1
        out.append(struct.pack('<HI', (code << 6) | 0x3F, len(body)) if (was_long or len(body) >= 0x3F) else
                   struct.pack('<H', (code << 6) | len(body)))
        out.append(body)
    assert done == 1, done
    res = bytearray(b''.join(out))
    struct.pack_into('<I', res, 4, len(res))
    return bytes(res)


def set_edit_align(movie, ids, align=2):
    """무비 맨 위 DefineEditText(37) 중 ids 글상자의 정렬 값만 바꿈(0 왼쪽, 1 오른쪽, 2 가운데). 길이 그대로."""
    rep = {}
    for code, p, ln in swf_tags.tags(movie):
        if code != 37:
            continue
        body = bytearray(movie[p:p + ln])
        cid = struct.unpack_from('<H', body, 0)[0]
        if cid not in ids:
            continue
        _, q = gfxfont.read_rect(bytes(body), 2)
        f1, f2 = body[q], body[q + 1]
        q += 2
        if f1 & 0x01:
            q += 2
        if f2 & 0x80:
            q = bytes(body).index(b'\0', q) + 1
        if f1 & 0x01 or f2 & 0x80:
            q += 2
        if f1 & 0x04:
            q += 4
        if f1 & 0x02:
            q += 2
        assert f2 & 0x20, cid
        log('정렬 바꿈', cid, body[q], '->', align)
        body[q] = align
        rep[p] = bytes(body)
    assert len(rep) == len(ids), (len(rep), ids)
    return swf_tags.rebuild(movie, rep)


# 옵션 화면 컨트롤러 그림 이름표(왼쪽 143 오른쪽 정렬, 오른쪽 146 왼쪽 정렬): 갈색 상자가 일본어 글자 폭으로 잡혀
# 한글(어그로 원래 폭)은 한쪽으로 쏠림 → 가운데 정렬
# Cemu 시험 결과 효과 없음(CLIK 버튼 부품이 autoSize 로 정렬을 덮어씀, 11/06) → 빈 집합으로 끔
OPTIONMENU_CENTER = set()

# 11/17: 이름표 Label 은 상자 폭 = textWidth + 왼쪽 여백 + 오른쪽 여백 + 5(스크립트 calculateWidth), 디자인 여백이 좌우 달라
# 원래부터 치우침(144: 왼 12·오 8, 147: 왼 8·오 15.5, 배경 폭 66). 스크립트는 두고 스프라이트 안 글상자 가로 위치만 옮겨
# 글자 양옆 공간을 같게(계산값) — {스프라이트: (글상자 번호, 원래 x, 새 x)}
LABEL_FIELD_X = {144: (143, 14.0, 11.5), 147: (146, 10.0, 14.25)}


class _Bits:
    def __init__(self, b, p):
        self.b, self.p, self.bit = b, p, 0

    def u(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | ((self.b[self.p] >> (7 - self.bit)) & 1)
            self.bit += 1
            if self.bit == 8:
                self.bit, self.p = 0, self.p + 1
        return v

    def s(self, n):
        v = self.u(n)
        return v - (1 << n) if n and v & (1 << (n - 1)) else v

    def end(self):
        return self.p + (1 if self.bit else 0)


def _read_matrix(b, p):
    r = _Bits(b, p)
    m = {'scale': None, 'rot': None}
    if r.u(1):
        n = r.u(5)
        m['scale'] = (r.s(n), r.s(n))
    if r.u(1):
        n = r.u(5)
        m['rot'] = (r.s(n), r.s(n))
    n = r.u(5)
    m['t'] = (r.s(n), r.s(n))
    return m, r.end()


def _write_matrix(m):
    bits = []

    def put(v, n):
        bits.extend((v >> (n - 1 - i)) & 1 for i in range(n))

    def nbits(*vals):
        return max(1, max((abs(v).bit_length() + 1) for v in vals)) if vals else 1

    for key in ('scale', 'rot'):
        pair = m[key]
        if pair is None:
            put(0, 1)
        else:
            put(1, 1)
            n = nbits(*pair)
            put(n, 5)
            for v in pair:
                put(v & ((1 << n) - 1), n)
    tx, ty = m['t']
    n = nbits(tx, ty) if (tx or ty) else 0
    put(n, 5)
    for v in (tx, ty):
        if n:
            put(v & ((1 << n) - 1), n)
    while len(bits) % 8:
        bits.append(0)
    return bytes(int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8))


def move_fields_in_sprites(movie, moves):
    """맨 위 DefineSprite(39) 안 PlaceObject2(26) 중 moves 의 글상자 가로 위치(tx)만 바꿔 스프라이트 태그를 다시 씀."""
    rep = {}
    done = 0
    for code, p, ln in swf_tags.tags(movie):
        if code != 39:
            continue
        sid = struct.unpack_from('<H', movie, p)[0]
        if sid not in moves:
            continue
        cid_want, x_old, x_new = moves[sid]
        body = movie[p:p + ln]
        out = [body[:4]]
        q = 4
        while q < len(body):
            cl = struct.unpack_from('<H', body, q)[0]
            c, l = cl >> 6, cl & 0x3F
            hl = 2
            if l == 0x3F:
                l = struct.unpack_from('<I', body, q + 2)[0]
                hl = 6
            tb = body[q + hl:q + hl + l]
            if c == 26 and tb[0] & 0x02 and tb[0] & 0x04 and struct.unpack_from('<H', tb, 3)[0] == cid_want:
                m, mend = _read_matrix(tb, 5)
                assert m['t'][0] == round(x_old * 20), (sid, m)
                m['t'] = (round(x_new * 20), m['t'][1])
                tb = tb[:5] + _write_matrix(m) + tb[mend:]
                chk, _ = _read_matrix(tb, 5)
                assert chk == m, (chk, m)
                done += 1
                log('이름표 글상자 위치', sid, cid_want, x_old, '->', x_new)
            out.append(struct.pack('<HI', (c << 6) | 0x3F, len(tb)) if (hl == 6 or len(tb) >= 0x3F)
                       else struct.pack('<H', (c << 6) | len(tb)))
            out.append(tb)
            q += hl + l
            if c == 0:
                break
        rep[p] = b''.join(out)
    assert done == len(moves), (done, moves)
    return swf_tags.rebuild(movie, rep)


def build_devilsthirdgame(old_swf, new_swf, tv_chars):
    """DevilsThirdGame.xxx(통째 압축) 안 fonts_en 사본도 같은 새 무비로 바꿈.
    게임 시작 때 늘 올라오는 패키지라 실제로는 이 사본이 쓰일 수 있음(UI_Fonts.xxx 만 고친 첫 빌드에서 한글이 네모)."""
    raw = open(os.path.join(COOKED, 'DevilsThirdGame.xxx'), 'rb').read()
    inner = ue3full.unpack(raw)
    pk, body, names, imps, exps = ue3pkg.tables(inner)
    assert not pk.chunks
    hits = [i for i, e in enumerate(exps) if e['class'] == 'SwfMovie' and e['name'] == 'fonts_en']
    assert len(hits) == 1, hits
    k = hits[0]
    e = exps[k]
    exp = body[e['offset']:e['offset'] + e['size']]
    if ue3pkg.get_array_prop(exp, names, 'RawData') != old_swf:
        raise SystemExit('DevilsThirdGame 의 fonts_en 이 UI_Fonts 와 다름')
    rep = {k: ue3pkg.set_array_prop(exp, names, 'RawData', new_swf)}
    # TVWarning(GamePad 전용일 때 TV 알림): fonts_en 가져오기 대신 한글 NewCez 일부를 무비에 직접 넣음
    tv = [i for i, e in enumerate(exps) if e['class'] == 'SwfMovie' and e['name'] == 'TVWarning']
    assert len(tv) == 1, tv
    if not EMBED_TV_FONT:
        tv = []
    checks = [(k, new_swf)]
    om = [i for i, e in enumerate(exps) if e['class'] == 'SwfMovie' and e['name'] == 'optionmenu']
    assert len(om) == 1, om
    if not (OPTIONMENU_CENTER or LABEL_FIELD_X):
        om = []
    oe = exps[om[0]] if om else None
    if oe:
        oexp = body[oe['offset']:oe['offset'] + oe['size']]
        om_movie = ue3pkg.get_array_prop(oexp, names, 'RawData')
        if OPTIONMENU_CENTER:
            om_movie = set_edit_align(om_movie, OPTIONMENU_CENTER)
        if LABEL_FIELD_X:
            om_movie = move_fields_in_sprites(om_movie, LABEL_FIELD_X)
        rep[om[0]] = ue3pkg.set_array_prop(oexp, names, 'RawData', om_movie)
        checks.append((om[0], om_movie))
    if tv:
        te = exps[tv[0]]
        texp = body[te['offset']:te['offset'] + te['size']]
        movie = ue3pkg.get_array_prop(texp, names, 'RawData')
        font_body, nglyph = subset_font(new_swf, SENTENCE_FONT, tv_chars, 1)
        new_movie = embed_font_for_import(movie, font_body)
        rep[tv[0]] = ue3pkg.set_array_prop(texp, names, 'RawData', new_movie)
        checks.append((tv[0], new_movie))
        log('TVWarning 글꼴 직접 넣음', SENTENCE_FONT, '글리프', nglyph, '무비', len(movie), '->', len(new_movie))
    new_inner = ue3pkg.repack(inner, rep)
    # 검증: 다시 읽어서 무비가 새 것인지
    pk2, body2, names2, imps2, exps2 = ue3pkg.tables(new_inner)
    for i, want in checks:
        e2 = exps2[i]
        assert ue3pkg.get_array_prop(body2[e2['offset']:e2['offset'] + e2['size']], names2, 'RawData') == want
    log('DevilsThirdGame fonts_en·TVWarning 교체, 풀린 크기', len(inner), '->', len(new_inner))
    return ue3full.pack(new_inner, 6), len(new_inner)


def font_replacements(tbl, chars, keep, skip_chars, tag):
    """패키지(풀린 바이트) 안 SubtitleFont·SkipFont 에 한글을 넣은 익스포트 교체표 {번호: 새 데이터}.
    SubtitleFont 사본은 VGSBase_LOC_JPN 과 UI_Fonts 두 곳에 있음(GamePad 알림 등은 UI_Fonts 쪽 사본으로 그림)."""
    pk, body, names, imps, exps = tbl  # ue3pkg.tables 결과(청크 패키지도 풀린 몸통 기준)
    getb = lambda e: bytes(body[e['offset']:e['offset'] + e['size']])
    rep = {}
    fi = [i for i, e in enumerate(exps) if e['class'] == 'Font' and e['name'] == 'SubtitleFont']
    assert len(fi) == 1, fi
    font_exp = getb(exps[fi[0]])
    _, props, _ = ue3font.parse_font(font_exp, names)
    tex = [p for p in props if p.name == 'Textures'][0].raw
    n = struct.unpack('>i', tex[:4])[0]
    refs = [r - 1 for r in struct.unpack('>%di' % n, tex[4:])]
    page_exps = [getb(exps[r]) for r in refs]
    sizes = [(512, 1024) if exps[r]['size'] > 500000 else ((512, 256) if exps[r]['size'] < 200000 else (512, 512))
             for r in refs]
    new_font, new_pages, report, imgs = subfont.inject_natural(font_exp, names, page_exps, sizes, chars, TTF_SUB, keep,
                                                               redraw=REDRAW, hint=SUB_HINT)
    assert len(new_font) == len(font_exp)
    if PUNCT_LEFT_PAD:
        # 11/18 사용자 「해! 가 너무 딱 붙어」 → 「!」「?」 잉크 왼쪽에 2px(한글 칸 오른쪽 여백 0px 이라 붙어 보임)
        new_font, new_pages, prep = subfont.pad_cells(new_font, names, new_pages, sizes, '!?', PUNCT_LEFT_PAD)
        log(tag, '부호 앞 여백', prep)
    if ELLIPSIS_LEFT_PAD:
        new_font, new_pages, erep = subfont.pad_cells(new_font, names, new_pages, sizes, '…', ELLIPSIS_LEFT_PAD)
        log(tag, '말줄임표 앞 여백', erep)
    rep[fi[0]] = new_font
    for r, b in zip(refs, new_pages):
        assert len(b) == exps[r]['size']
        rep[r] = b
    log(tag, 'SubtitleFont 새 칸', len(report))
    # SkipFont: 「Ⓐ 건너뛰기」 글자를 칸을 늘려 덧붙임(가나 잉크 높이 19px·위 5px 에 맞춤)
    si = [i for i, e in enumerate(exps) if e['class'] == 'Font' and e['name'] == 'SkipFont']
    assert len(si) == 1, si
    sk = getb(exps[si[0]])
    _, sprops, _ = ue3font.parse_font(sk, names)
    stex = [p for p in sprops if p.name == 'Textures'][0].raw
    sr = struct.unpack('>i', stex[4:8])[0] - 1
    if SKIP_REUSE:
        # 11/18 칸을 덧붙인 판은 컷신 스킵 안내 「건너뛰기」가 「IKAE」로 그려짐(실기·Cemu, 음성 무관) →
        # 칸 수를 원본(13)대로 두고 안 쓰는 「キスップ」 칸에 다시 그림 → Cemu 에서 「Ⓐ 건너뛰기」 정상(11/18 사용자 확인)
        olds = [c for c in 'キスップ']
        assert len(skip_chars) <= len(olds), skip_chars
        new_sk, new_sp, srep, simg = subfont.reuse_cells(sk, names, getb(exps[sr]), (256, 64),
                                                         list(zip(olds, skip_chars)), TTF_SUB, 19, 5)
    else:
        new_sk, new_sp, srep, simg = subfont.append_cells(sk, names, getb(exps[sr]), (256, 64), skip_chars, TTF_SUB, 19, 5)
    rep[si[0]] = new_sk
    rep[sr] = new_sp
    log(tag, 'SkipFont 덧붙인 칸', srep)
    return rep, report, imgs, simg


def build_vgsbase(chars, keep, skip_chars, loc='JPN'):
    """VGSBase_LOC_<loc> 의 SubtitleFont·SkipFont. INT·FRA 사본도 글자 표가 JPN 과 같고,
    컨트롤러 알림(실행 파일 FControllerNotice, UFont 로 직접 그림)은 기본 목차의 LOC_INT 쪽 폰트를 씀 → 셋 다 넣음."""
    raw = open(os.path.join(COOKED, 'VGSBase_LOC_%s.xxx' % loc), 'rb').read()
    inner = ue3full.unpack(raw)
    rep, report, imgs, simg = font_replacements(ue3pkg.tables(inner), chars, keep, skip_chars, 'VGSBase_' + loc)
    for r in report:
        log('subtitle', *r)
    for ti, im in enumerate(imgs):
        Image.fromarray(im[:, :, 3]).save(os.path.join(OUT, 'preview_subtitle_page%d.png' % ti))
    Image.fromarray(simg[:, :, 3]).resize((1024, 256), Image.NEAREST).save(os.path.join(OUT, 'preview_skipfont.png'))
    new_inner = ue3pkg.repack(inner, rep)
    return ue3full.pack(new_inner, 6), len(new_inner), report, imgs


def render_subtitle_line(report, imgs, text, path, scale=2):
    """새 칸으로 자막 한 줄을 그대로 이어 붙여 그림(원래 폭 확인용)."""
    cells = {r[0]: r for r in report}
    W = sum(cells[c][4] for c in text if c in cells) + 8
    im = np.zeros((48, W), np.uint8)
    x = 4
    for c in text:
        if c not in cells:
            continue
        ch, ti, su, sv, us, vs, top = cells[c]
        a = imgs[ti][sv:sv + vs, su:su + us, 3]
        y = 4 + top
        im[y:y + vs, x:x + us] = np.maximum(im[y:y + vs, x:x + us], a)
        x += us
    Image.fromarray(im).resize((W * scale, 48 * scale), Image.NEAREST).save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'build_log.txt'), 'w').close()
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    rows = json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
    src = {r['key']: r['jp'] for r in rows}
    hangul = sorted({c for v in ko.values() for c in v if 0xAC00 <= ord(c) <= 0xD7A3})
    log('hangul chars', len(hangul))

    coal, files = build_coalesced(ko, src)
    write('DevilsThirdGame/CookedWiiU/Coalesced_JPN.bin', coal)
    keep = bt.used_chars(files)
    log('번역 뒤 쓰이는 글자', len(keep))

    skip_chars = sorted({c for c in ko['DT_UI_Labels|Misc|MovieSkip'] if 0xAC00 <= ord(c) <= 0xD7A3})
    ui, fonts, old_swf, new_swf = build_ui_fonts(hangul, keep, skip_chars)
    write('DevilsThirdGame/CookedWiiU/UI_Fonts.xxx', ui)
    # TVWarning 에 넣을 글자: 번역에 쓰인 모든 글자 + 영문·숫자·부호(ASCII)
    tv_chars = set(''.join(ko.values())) | {chr(c) for c in range(0x20, 0x7F)}
    dtg, dtg_usize = build_devilsthirdgame(old_swf, new_swf, tv_chars)
    write('DevilsThirdGame/CookedWiiU/DevilsThirdGame.xxx', dtg)
    us_txt = b'%d\r\n' % dtg_usize
    write('DevilsThirdGame/CookedWiiU/DevilsThirdGame.xxx.uncompressed_size', us_txt)
    bt.render_gfx_preview(fonts, '솔로 플레이 수용소에서 탈출하라', os.path.join(OUT, 'preview_gfx_fonts.png'))

    sizes = {'CookedWiiU/Coalesced_JPN.bin': (len(coal), None),
             'CookedWiiU/UI_Fonts.xxx': (len(ui), None)}
    for loc in ('JPN', 'INT', 'FRA'):
        vgs, vgs_usize, report, imgs = build_vgsbase(hangul, keep, skip_chars, loc)
        name = 'VGSBase_LOC_%s.xxx' % loc
        write('DevilsThirdGame/CookedWiiU/' + name, vgs)
        vgs_us_txt = b'%d\r\n' % vgs_usize  # SkipFont 칸이 늘어 풀린 크기가 바뀜
        write('DevilsThirdGame/CookedWiiU/' + name + '.uncompressed_size', vgs_us_txt)
        sizes['CookedWiiU/' + name] = (len(vgs), vgs_usize)
        sizes['CookedWiiU/' + name + '.uncompressed_size'] = (len(vgs_us_txt), None)
        if loc == 'JPN':
            render_subtitle_line(report, imgs, '이게 정보국 데이터베이스에 있던 “차르 벨”에 관한 전부다',
                                 os.path.join(OUT, 'preview_subtitle_line.png'))

    sizes.update({
             'CookedWiiU/DevilsThirdGame.xxx': (len(dtg), dtg_usize),
             'CookedWiiU/DevilsThirdGame.xxx.uncompressed_size': (len(us_txt), None)})
    bt.update_toc(sizes)
    log('done')


if __name__ == '__main__':
    main()
