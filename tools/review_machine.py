"""7단계 기계 검사 → work/review/machine.json, work/review/machine_summary.txt

문제(규칙 위반이 분명)
- 마침표 누락: 자막·대사·설명·메시지의 값 끝이 한글 종결형인데 부호 없음(비명·웃음뿐인 줄, 라벨·메뉴 제외)
- 그녀·그들 한 값에 두 번 이상 / 전각 영숫자·！？ 남음 / 띄어쓰기 두 칸(들여쓰기 제외)·부호 앞 공백
확인(사람이 봐야 함)
- 줄 끝 종결형인데 부호 없음(값 중간 줄: 호칭·도치 앞 줄바꿈일 수 있음)
- 직역투 낱말(이 내가, 해 버렸, 에 대해, 이것을·그것을·저것을, 하는 것이다, 과연, 어떻게든)
- 숫자 불일치(원문 숫자가 번역에 없음)
- 길이 비율(원문 6자 이상, 번역/원문 < 0.45 또는 > 2.6)
- 높임 섞임: 같은 장면에서 같은 화자의 문장 끝이 존댓말·반말로 갈림(소수 쪽 줄을 표시)
- 한자어 대조: 원문 한자어(2~4자)의 한국 한자음이 번역에 없음
- UI 같은 원문 다른 번역(12자 이하, 자막 제외)
"""
import collections
import json
import os
import re

import hanja

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAGS = re.compile(r'~/?COL[^~]*~|#[A-Za-z_]+#')
SENT_END = re.compile(r'[가-힣](?<![가-힣]\s)$')
END_WORDS = re.compile(r'(다|요|까|지|네|군|야|어|아|라|자|냐|니|게|세|오|죠|래|걸|데|나|고|해|와|줘|돼|봐|마|가|든|쇼|소|구먼|구나|니다)$')
INTERJ = re.compile(r'^[\s“‘(]*([으아앗악윽흑헉하호후히헤우오에이흐햐핫킥큭크쿠캬끄그와워읏읍흡흥헐허]|하하|크크)+[!?…~\-]*[”’)]?$')
POLITE = re.compile(r'(습니다|습니까|니다|세요|에요|예요|해요|어요|아요|지요|죠|군요|네요|시오|십시오|ㅂ니다|겠습니까)[.!?…]*$')
PLAIN = re.compile(r'(다|냐|니|지|야|어|아|해|자|라|군|네|걸|마|래|게|구나|거든|잖아|는데|던데)[.!?…]*$')
LITERAL = ['이 내가', '해 버렸', '해버렸', '에 대해', '이것을', '그것을', '저것을', '하는 것이다', '인 것이다', '과연', '어떻게든', '라고 할까']
FULLW = re.compile(r'[０-９Ａ-Ｚａ-ｚ！？]')
KANJI_WORD = re.compile(r'[一-鿿]{2,4}')
NUM = re.compile(r'\d+')
UI_GROUPS = {'ui', 'mp', 'weapon'}
SENT_GROUPS = {'story_sub', 'tips', 'collect'}


def load():
    src = [x for x in json.load(open(os.path.join(ROOT, 'work', 'extract', 'text_jpn.json'), encoding='utf-8'))
           if x['scope'] == 'solo']
    ko = json.load(open(os.path.join(ROOT, 'work', 'translation', 'ko.json'), encoding='utf-8'))
    for x in src:
        x['ko'] = ko[x['key']]
    return src


def is_sentence_value(x):
    """마침표가 필요한 값인가: 자막·팁·수집품 설명·메시지 창 문장·임무 브리핑. 라벨·메뉴·제목은 아님."""
    if x['group'] in SENT_GROUPS:
        return not (x['group'] == 'collect' and x['section'] in ('Labels', 'Category', 'Locations'))
    if x['file'] == 'DT_UI_MessageBox':
        return x['section'] != 'Titles'
    if x['section'] in ('Descriptions', 'Menus_Descriptions', 'SoloplayMenuDescriptions', 'NormalWeapons_Descriptions'):
        return True
    return False


def main():
    items = load()
    res = collections.defaultdict(list)

    def add(cat, x, note=''):
        res[cat].append({'key': x['key'], 'speaker': x.get('speaker'), 'jp': x['jp'], 'ko': x['ko'], 'note': note})

    for x in items:
        ko = TAGS.sub('', x['ko'])
        jp = TAGS.sub('', x['jp'])
        lines = [l.strip() for l in ko.split('\n')]
        if is_sentence_value(x):
            nonempty = [l for l in lines if l]
            if nonempty:
                last = nonempty[-1]
                if re.search(r'[가-힣]$', last) and END_WORDS.search(last) and not INTERJ.match(last):
                    add('문제:마침표 누락(값 끝)', x, last)
                for l in nonempty[:-1]:
                    if re.search(r'[가-힣]$', l) and END_WORDS.search(l) and not INTERJ.match(l):
                        add('확인:줄 끝 부호 없음(값 중간)', x, l)
        if ko.count('그녀') >= 2 or ko.count('그들') >= 2:
            add('문제:그녀·그들 반복', x)
        if FULLW.search(ko):
            add('문제:전각 문자', x, ''.join(FULLW.findall(ko)))
        # 변수(#Name#)를 지우면 양옆 공백이 붙어 두 칸처럼 보이므로 자리 채움 글자로 바꿔서 봄
        for l in TAGS.sub('X', x['ko']).split('\n'):
            body = l.lstrip(' 　\t')
            if '  ' in body.rstrip():
                add('문제:띄어쓰기 두 칸', x, l)
                break
        if re.search(r' [.,!?]', ko):
            add('문제:부호 앞 공백', x)
        for w in LITERAL:
            if w in ko:
                add('확인:직역투 낱말', x, w)
        jn = [n.lstrip('0') or '0' for n in NUM.findall(re.sub(r'(?<=\d) (?=\d)', '', jp.translate(str.maketrans('０１２３４５６７８９', '0123456789'))))]
        kn = [n.lstrip('0') or '0' for n in NUM.findall(ko)]
        miss = [n for n in jn if n not in kn]
        if miss:
            add('확인:숫자 불일치', x, ' '.join(miss))
        if len(jp) >= 6:
            r = len(ko) / len(jp)
            if r < 0.45 or r > 2.6:
                add('확인:길이 비율', x, '%.2f' % r)
        for w in set(KANJI_WORD.findall(jp)):
            reading = hanja.translate(w, 'substitution')
            if re.fullmatch('[가-힣]+', reading) and reading not in ko.replace(' ', ''):
                res['_hanja'].append({'key': x['key'], 'word': w, 'reading': reading, 'jp': x['jp'], 'ko': x['ko']})
    # 높임 섞임(같은 장면·같은 화자)
    scenes = collections.defaultdict(list)
    for x in items:
        if x['group'] == 'story_sub':
            scenes[(x['file'], x['section'], x.get('speaker'))].append(x)
    for k, xs in scenes.items():
        pol, pl = [], []
        for x in xs:
            for s in re.split(r'(?<=[.!?])\s+|\n', TAGS.sub('', x['ko'])):
                s = s.strip()
                if POLITE.search(s):
                    pol.append(x)
                elif PLAIN.search(s):
                    pl.append(x)
        if pol and pl:
            minority = pol if len(pol) < len(pl) else pl
            for x in {m['key']: m for m in minority}.values():
                add('확인:높임 섞임(장면·화자)', x, '%s 존댓말 %d / 반말 %d' % (k[1], len(pol), len(pl)))
    # 한자어: 같은 낱말이 3번 이상 다르게 빠진 것만(노이즈 줄이기)
    hc = collections.Counter(h['word'] for h in res['_hanja'])
    for h in res.pop('_hanja'):
        if hc[h['word']] >= 1:
            res['확인:한자어 대조'].append({'key': h['key'], 'speaker': None, 'jp': h['jp'], 'ko': h['ko'],
                                         'note': '%s(%s)' % (h['word'], h['reading'])})
    # UI 같은 원문 다른 번역
    by = collections.defaultdict(set)
    for x in items:
        if x['group'] in UI_GROUPS and len(x['jp']) <= 12:
            by[x['jp']].add(x['ko'])
    for x in items:
        if x['group'] in UI_GROUPS and len(by.get(x['jp'], ())) > 1:
            add('확인:같은 원문 다른 번역(UI)', x, ' / '.join(sorted(by[x['jp']])))
    os.makedirs(os.path.join(ROOT, 'work', 'review'), exist_ok=True)
    json.dump(res, open(os.path.join(ROOT, 'work', 'review', 'machine.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    out = []
    for cat in sorted(res):
        out.append('%s\t%d' % (cat, len(res[cat])))
        for r in res[cat][:6]:
            out.append('    %s | %s | %s || %s' % (r['key'], r['note'], r['jp'].replace('\n', '/')[:50], r['ko'].replace('\n', '/')[:60]))
    open(os.path.join(ROOT, 'work', 'review', 'machine_summary.txt'), 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
