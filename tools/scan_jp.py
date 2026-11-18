"""전체 패키지(.xxx·.upk)를 풀어 일본어 문자열과 언어 이름이 붙은 오브젝트를 찾는다.

문자열 판정(노이즈 방지):
  - UE3 FString: i32 BE 음수 길이 -n, 뒤에 UTF-16LE n글자(마지막은 0). 글자가 모두 '글 문자' 범위이고
    가나 1자 이상 또는 한자 2자 이상이면 일본어.
  - UTF-8(SWF 등): 0 바이트로 둘러싸인 문자열이 위 조건을 만족하면 일본어(HTML 태그는 빼고 판정).
- 픽셀·소리·지형처럼 글이 없는 큰 클래스는 건너뛴다(SKIP).
- 언어 이름: 오브젝트 이름에 _jp/_ja/_jpn/_en/_eng/_int/_fr/_fra 등이 붙은 것
출력: work/survey/jp_strings.json, work/survey/lang_named.json
사용: python -I tools/scan_jp.py [프로세스 수]
"""
import json
import os
import re
import struct
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402

ROOT = os.path.dirname(HERE)
COOKED = os.path.join(ROOT, 'Devils Third [Game] [0005000010138f00]', 'content', 'DevilsThirdGame', 'CookedWiiU')
SKIP = {'Texture2D', 'LightMapTexture2D', 'ShadowMapTexture2D', 'ShadowMap1D', 'StaticMesh', 'SkeletalMesh',
        'AnimSequence', 'Model', 'Polys', 'SoundNodeWave', 'TextureCube', 'TerrainWeightMapTexture',
        'ShaderCache', 'FracturedStaticMesh', 'LightMapTexture2DCompressed', 'PhysicsAsset', 'RB_BodySetup',
        'Level', 'Terrain', 'TextureMovie', 'ApexClothingAsset', 'LandscapeHeightfieldCollisionComponent',
        'NavigationMeshBase', 'BrushComponent'}
KANA = re.compile('[぀-ヿ]')
KANJI = re.compile('[一-鿿]')
TEXTY = re.compile('^[\t\n\r -~ -ÿ‐-‿←-⇿①-⓿'
                   '■-⛿　-ヿ一-鿿＀-￯]+$')
FSTR = re.compile(rb'\xff\xff[\xc0-\xff][\x00-\xff]|\xff\xff\xff[\x00-\xff]')
CSTR8 = re.compile(rb'\x00([^\x00]{3,}?)(?=\x00)')
HAS8 = re.compile(rb'[\xe3-\xe9]')
LANG = re.compile(r'(?i)(?:^|[_\-.])(jp|ja|jpn|jap|japan|japanese|en|eng|int|us|fr|fra|french|kr|ko|kor)(?:$|[_\-.\d])')


def is_jp(s):
    return bool(TEXTY.match(s)) and (bool(KANA.search(s)) or len(KANJI.findall(s)) >= 2)


def scan_bytes(b):
    out = []
    for m in FSTR.finditer(b):
        i = m.start()
        n = -struct.unpack_from('>i', b, i)[0]
        if n < 2 or n > 20000:
            continue
        seg = b[i + 4:i + 4 + n * 2]
        if len(seg) != n * 2 or seg[-2:] != b'\x00\x00':
            continue
        try:
            t = seg[:-2].decode('utf-16-le')
        except UnicodeDecodeError:
            continue
        if is_jp(t):
            out.append(('fstr', t))
    for m in CSTR8.finditer(b):
        raw = m.group(1)
        if not HAS8.search(raw):
            continue
        try:
            t = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if is_jp(re.sub('<[^>]*>', '', t)):
            out.append(('utf8', t))
    return out


def one(name):
    path = os.path.join(COOKED, name)
    try:
        raw = open(path, 'rb').read()
        if raw[:4] == b'\x9e\x2a\x83\xc1' and struct.unpack_from('>I', raw, 4)[0] == 0x20000:
            raw = ue3full.unpack(raw)
        pk, body, names, imps, exps = ue3pkg.tables(raw)
    except Exception as e:  # noqa: BLE001
        return name, [['!error', '', '', repr(e)]], []
    found = []
    langs = []
    for e in exps:
        if LANG.search(e['name']):
            langs.append((e['class'], e['name']))
        if e['class'] in SKIP:
            continue
        b = body[e['offset']:e['offset'] + e['size']]
        for kind, s in scan_bytes(b):
            found.append([e['class'], e['name'], kind, s])
    return name, found, langs


def main():
    names = sorted(n for n in os.listdir(COOKED) if n.endswith('.xxx') or n.endswith('.upk'))
    procs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    res = {}
    lang = {}
    with Pool(procs) as p:
        for name, found, langs in p.imap_unordered(one, names, chunksize=2):
            if found:
                res[name] = found
            if langs:
                lang[name] = langs
    S = os.path.join(ROOT, 'work', 'survey')
    json.dump(res, open(os.path.join(S, 'jp_strings.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(lang, open(os.path.join(S, 'lang_named.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('packages with jp', len(res), 'strings', sum(len(v) for v in res.values()),
          'lang-named packages', len(lang), 'objects', sum(len(v) for v in lang.values()))


if __name__ == '__main__':
    main()
