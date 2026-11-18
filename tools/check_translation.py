"""번역 결과 검사(번역 담당·합치기 공용).

입력: {"key": "번역문"} JSON (key = 파일|구역|이름, text_jpn.json 과 같은 키)
검사:
  누락·여분 키 / 태그·변수 개수(~COL(..)~ ~/COL~ #..# Ⓐ❶~❹ %s) / 줄바꿈 수 ≤ 원문 / 앞뒤 공백 모양
  남은 일본어(가나·한자) / 「」『』 / 부호(…. ~. ~, 띄운 ! ?) / 금지 표기 / 폭(자막 px, UI em)
폭 계산: 최종 글꼴 어그로체 원래 폭 기준
  자막: 한글 = 어그로 M 진행 폭(실제 크기 '国' 21px), 나머지 글자 = 원본 자막 폰트 칸 폭, 한도 688px
  UI: 한글·띄어쓰기 = 어그로 M 진행 폭 × OptiB 배율, 나머지 = OptiB 진행 폭, 한도 limits.json 의 w_em
사용: python -I -X utf8 tools/check_translation.py <번역.json> [--src work/extract/text_jpn.json] [--quiet]
종료 코드: 문제 수(최대 255)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)

TAG = re.compile(r'~/?COL[^~]*~|#[A-Za-z_]+#|[Ⓐ-ⓩ❶-❿①-⑳]|%[0-9.]*[sdif]')
JPCH = re.compile(r'[぀-ヿ一-鿿々]')
BAD_PUNCT = [('….', '말줄임표 뒤 마침표'), ('~.', '물결표 뒤 마침표'), ('~,', '물결표 뒤 쉼표'),
             (' !', '느낌표 앞 띄어쓰기'), (' ?', '물음표 앞 띄어쓰기'), ('「', '「」 남음'), ('」', '「」 남음'),
             ('『', '『』 남음'), ('』', '『』 남음'), ('!.', '!.'), ('?.', '?.'), ('..', '마침표 두 개')]
# 11/18 영어판(영어 음성) 기준으로 바꿈: 아이반→이반, 장관→국장, 그레네이드→수류탄, 코르치크→카시탄 (라저·데브그루는 그대로, 사용자 결정)
FORBID = [('아이번', '아이반'), ('이반', '아이반(11/18 영어 음성도 아이반)'),('장관', '국장(캐러웨이)'), ('로저', '라저'), ('그레네이드', '수류탄'),
          ('예스 서', '알겠습니다'), ('염백', '엔바쿠'), ('코르치크', '카시탄'), ('코르티크', '카시탄'), ('카슈탄', '카시탄'),
          ('짜르', '차르'), ('신드롬', '증후군'), ('DEVGRU', '데브그루'),
          ('사하', '샤하'), ('테리블', '테러블'), ('이 내가', '내가'), ('그녀', '이름·호칭(반복 금지)')]


def lead(s):
    return re.match(r'^[\s　]*', s).group(0)


def trail(s):
    return re.search(r'[\s　]*$', s).group(0)


class Widths:
    def __init__(self):
        import gfxfont  # noqa: F401
        import hangul_gfx
        import measure
        import subfont
        from fontTools.ttLib import TTFont
        lim = json.load(open(os.path.join(ROOT, 'work', 'survey', 'limits.json'), encoding='utf-8'))
        self.lim = lim['keys']
        import build_full
        ttf = build_full.TTF_SUB  # 빌드 자막 글꼴로 폭을 잰다(11/18 워헤이븐 굵게)
        # 자막
        self.sj = measure.sub_font(os.path.join(measure.COOKED, 'VGSBase_LOC_JPN.xxx'), True)
        self.rnd = subfont.Renderer(ttf, 21, 10)
        # UI: OptiB 배율
        gf = measure.gfx_font()
        self.gf = gf
        import font_compare
        f = font_compare.gfx_fonts()['OptiB-NewRodinB85-NTLGDB002']
        i = f.codes.index(ord('国'))
        import gfxfont as gx
        rc, _ = gx.decode_shape(f.shapes[i])
        ui_ttf = build_full.TTF_M  # OptiB 는 메뉴 M 자리(워헤이븐 보통)
        src = hangul_gfx.HangulSource(ui_ttf)
        tf = hangul_gfx.make_transform(src, hangul_gfx.ink_box(rc), f.layout['adv'][i])
        self.s = tf.s
        tt = TTFont(ui_ttf)
        self.cmap = tt.getBestCmap()
        self.hmtx = tt['hmtx']
        self.sub_cache = {}
        self.sec_max = {}
        ex = os.path.join(ROOT, 'work', 'translation', 'width_exceptions.json')
        self.exceptions = set(json.load(open(ex, encoding='utf-8'))) if os.path.exists(ex) else set()
        self.all_rows = json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))

    def sub_px(self, line):
        w = 0
        for c in line:
            o = ord(c)
            if 0xAC00 <= o <= 0xD7A3 or c in '“”‘’':
                if c not in self.sub_cache:
                    self.sub_cache[c] = self.rnd.font.getlength(c)
                w += self.sub_cache[c]
            elif c == ' ':
                w += self.rnd.font.getlength(' ')
            else:
                w += self.sj.get(o, self.sj[ord('国')])
        return w

    def ui_em(self, line):
        w = 0
        for c in line:
            o = ord(c)
            if 0xAC00 <= o <= 0xD7A3 or c == ' ':
                w += self.hmtx[self.cmap[o]][0] * self.s
            else:
                w += self.gf.get(o, self.gf[ord('国')])
        return w / 20480


def check(tr, src_rows, widths=None, sub_limit=688):
    rows = {r['key']: r for r in src_rows}
    issues = []
    for k in rows:
        if rows[k]['scope'] == 'solo' and k not in tr:
            issues.append((k, '번역 없음'))
    for k, ko in tr.items():
        if k not in rows:
            issues.append((k, '원문에 없는 키'))
            continue
        r = rows[k]
        jp = r['jp']
        if sorted(TAG.findall(jp)) != sorted(TAG.findall(ko)):
            issues.append((k, '태그·변수 다름 원문%s 번역%s' % (sorted(TAG.findall(jp)), sorted(TAG.findall(ko)))))
        if ko.count('\n') > jp.count('\n'):
            issues.append((k, '줄바꿈 늘어남 %d > %d' % (ko.count('\n'), jp.count('\n'))))
        if lead(ko) != lead(jp) or trail(ko) != trail(jp):
            issues.append((k, '앞뒤 공백 모양 다름'))
        plain = TAG.sub('', ko)
        if JPCH.search(plain):
            issues.append((k, '일본어 남음: %s' % ''.join(sorted(set(JPCH.findall(plain))))))
        for p, why in BAD_PUNCT:
            if p in plain:
                issues.append((k, '부호: ' + why))
        for bad, good in FORBID:
            if bad == '사하':
                # 이름으로 따로 쓰인 것만(구사하는·종사하는 같은 낱말 안은 제외)
                if not re.search(r'(?<![가-힣])%s(?![가-힣])' % bad, plain) and '그룬들라 사하' not in plain:
                    continue
            if bad == '이반':
                if not re.search(r'(?<![가-힣])이반', plain):
                    continue  # 「아이반」 안의 이반은 제외
            if bad in plain and bad not in TAG.sub('', jp):
                if bad == '그녀' and plain.count('그녀') < 2:
                    continue
                issues.append((k, '금지 표기 「%s」 → %s' % (bad, good)))
        if widths and k in widths.lim and k not in widths.exceptions:
            L = widths.lim[k]
            lines = re.sub(r'~/?COL[^~]*~', '', ko).split('\n')
            if L['kind'] == 'subtitle':
                for i, ln in enumerate(lines):
                    px = widths.sub_px(ln)
                    if px > sub_limit:
                        issues.append((k, '자막 폭 넘침 %d줄 %dpx > %d' % (i + 1, px, sub_limit)))
            else:
                lim = L['w_em']
                # 자동 줄바꿈 글상자(영·프가 한 줄로 길게 들어 있음): 일본어 원문 최대 줄 폭을 한도로
                if jp.count('\n') >= 2 and lim > 40:
                    # 같은 파일|구역 일본어 원문 전체에서 가장 긴 줄 = 글상자 폭으로 봄
                    sec = k.rsplit('|', 1)[0]
                    if sec not in widths.sec_max:
                        widths.sec_max[sec] = max(widths.ui_em(x) for r2 in widths.all_rows if r2['key'].startswith(sec + '|')
                                                  for x in re.sub(r'~/?COL[^~]*~', '', r2['jp']).split('\n'))
                    lim = widths.sec_max[sec]
                for i, ln in enumerate(lines):
                    em = widths.ui_em(ln)
                    if em > lim + 0.001:
                        issues.append((k, 'UI 폭 넘침 %d줄 %.2fem > %.2fem' % (i + 1, em, lim)))
    return issues


def main():
    path = sys.argv[1]
    srcp = sys.argv[sys.argv.index('--src') + 1] if '--src' in sys.argv else os.path.join(ROOT, 'work', 'extract', 'text_jpn.json')
    tr = json.load(open(path, encoding='utf-8'))
    src = json.load(open(srcp, encoding='utf-8'))
    # 덩어리 검사면 그 덩어리 원문만 대상으로
    chunk_src = os.path.join(ROOT, 'work', 'translation', 'src', os.path.basename(path))
    if os.path.exists(chunk_src):
        keys = {r['key'] for r in json.load(open(chunk_src, encoding='utf-8'))}
        src = [r for r in src if r['key'] in keys]
    issues = check(tr, src, Widths())
    for k, m in issues:
        print('%s\t%s' % (k, m))
    print('검사 %d줄, 문제 %d' % (len(tr), len(issues)))
    sys.exit(min(len(issues), 255))


if __name__ == '__main__':
    main()
