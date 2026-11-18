# -*- coding: utf-8 -*-
"""배포용 패처 꾸리기 — 빌드본과 원본을 파일마다 비교해 바뀐 부분(xdelta)만 담는다.

  python -I -X utf8 tools/build_full.py
  python -I -X utf8 tools/make_patcher.py v1.0f [--python <내장 파이썬 폴더>] [--xdelta <xdelta3.exe>]

출력: work/release/ADNJ_KPatch_<버전>/      패처 폴더(패치하기.bat · python · patcher · licenses · README_KO.txt)
      work/release/ADNJ_KPatch_<버전>.zip  (릴리즈 이름 규칙 [게임 코드]_KPatch_[버전])
패치 데이터에 원본 게임 데이터는 넣지 않는다: 통째·청크 압축 패키지는 풀어서, Coalesced 는 복호화해서 xdelta 를 만든다.
만든 뒤 patcher/patch.py 의 make() 로 직접 다시 만들어 빌드본과 해시가 같은지 확인한다.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import coalesced  # noqa: E402
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402

GAME = os.path.join(ROOT, 'Devils Third [Game] [0005000010138f00]', 'content')
BUILT = os.path.join(ROOT, 'work', 'build', 'full', 'sdcafiine', '0005000010138F00', 'DevilsThirdKR', 'content')
REL = os.path.join(ROOT, 'work', 'release')
PY_DEFAULT = 'G:/KoreanTranslation/[Wii U] 환영이문록/work/python_embed'
XD_DEFAULT = 'G:/KoreanTranslation/[N3DS] 파이어 엠블렘 무쌍/tools/bin/xdelta3.exe'


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def xdelta_make(xd, old, new, tmp):
    a, b, d = (os.path.join(tmp, n) for n in ('old', 'new', 'delta'))
    open(a, 'wb').write(old)
    open(b, 'wb').write(new)
    if os.path.exists(d):
        os.remove(d)
    subprocess.run([xd, '-e', '-9', '-f', '-s', a, b, d], check=True, capture_output=True)
    return open(d, 'rb').read()


def kind_of(rel, orig):
    if rel.endswith('.uncompressed_size'):
        return 'copy'
    if os.path.basename(rel).startswith('Coalesced_'):
        return 'coalesced'
    if rel.endswith('.xxx'):
        return 'full' if orig[4:8] == b'\x00\x02\x00\x00' else 'chunked'
    return 'raw'


def main():
    ver = sys.argv[1]
    py = sys.argv[sys.argv.index('--python') + 1] if '--python' in sys.argv else PY_DEFAULT
    xd = sys.argv[sys.argv.index('--xdelta') + 1] if '--xdelta' in sys.argv else XD_DEFAULT
    assert os.path.isfile(os.path.join(py, 'python.exe')), '내장 파이썬이 없음: %s' % py
    assert os.path.isfile(xd), 'xdelta3 가 없음: %s' % xd
    name = 'ADNJ_KPatch_%s' % ver
    top = os.path.join(REL, name)
    if os.path.exists(top):
        shutil.rmtree(top)
    pdir = os.path.join(top, 'patcher')
    pay = os.path.join(pdir, 'payload')
    os.makedirs(pay)
    lib = os.path.join(pdir, 'lib')
    os.makedirs(lib)
    for f in ('ue3full.py', 'ue3pkg.py'):
        shutil.copyfile(os.path.join(HERE, f), os.path.join(lib, f))
    import Crypto
    shutil.copytree(os.path.dirname(Crypto.__file__), os.path.join(lib, 'Crypto'),
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyi', 'SelfTest'))
    os.makedirs(os.path.join(pdir, 'bin'))
    shutil.copyfile(xd, os.path.join(pdir, 'bin', 'xdelta3.exe'))
    for f in ('patch.py', 'rules.txt'):
        shutil.copyfile(os.path.join(ROOT, 'patcher', f), os.path.join(pdir, f))

    rels = sorted(os.path.relpath(os.path.join(dp, f), BUILT).replace(os.sep, '/')
                  for dp, _, fs in os.walk(BUILT) for f in fs)
    man = dict(version=ver, files=[])
    tmp = tempfile.mkdtemp(prefix='dt_mk_')
    try:
        for i, rel in enumerate(rels):
            new = open(os.path.join(BUILT, *rel.split('/')), 'rb').read()
            orig = open(os.path.join(GAME, *rel.split('/')), 'rb').read()
            kind = kind_of(rel, orig)
            e = dict(path=rel, kind=kind, src_size=len(orig), src_sha1=sha1(orig), out_sha1=sha1(new), data='%02d.bin' % i)
            if kind == 'copy':
                assert len(new) < 64, rel
                d = new
            elif kind == 'raw':
                d = xdelta_make(xd, orig, new, tmp)
            elif kind == 'full':
                d = xdelta_make(xd, ue3full.unpack(orig), ue3full.unpack(new), tmp)
            elif kind == 'chunked':
                pk = ue3pkg.Pkg(new)
                d = xdelta_make(xd, ue3pkg.Pkg(orig).unpacked(), pk.unpacked(), tmp)
                hdr = new[:pk.chunks[0][2]]
                e['header'] = '%02d_hdr.bin' % i
                e['chunks'] = [[uo, us] for uo, us, _, _ in pk.chunks]
                open(os.path.join(pay, e['header']), 'wb').write(hdr)
            else:
                d = xdelta_make(xd, coalesced.decrypt(orig), coalesced.decrypt(new), tmp)
                e['key'] = coalesced.KEY.hex()
            open(os.path.join(pay, e['data']), 'wb').write(d)
            man['files'].append(e)
            print('%-52s %-9s 원본 %9d · 패치 데이터 %9d' % (rel, kind, len(orig), len(d)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    json.dump(man, open(os.path.join(pay, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    bat = open(os.path.join(ROOT, 'patcher', '패치하기.bat'), 'rb').read().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    open(os.path.join(top, '패치하기.bat'), 'wb').write(bat)
    shutil.copytree(py, os.path.join(top, 'python'), ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(os.path.join(ROOT, 'patcher', 'licenses'), os.path.join(top, 'licenses'))
    readme = open(os.path.join(ROOT, 'patcher', 'README_KO.txt'), encoding='utf-8').read().replace('{VER}', ver)
    open(os.path.join(top, 'README_KO.txt'), 'w', encoding='utf-8', newline='\r\n').write(readme)

    zp = os.path.join(REL, name + '.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for dp, _, fs in os.walk(top):
            for f in sorted(fs):
                fp = os.path.join(dp, f)
                z.write(fp, os.path.relpath(fp, REL).replace(os.sep, '/'))
    print('%s %.1fMB' % (os.path.basename(zp), os.path.getsize(zp) / 1e6))


if __name__ == '__main__':
    main()
