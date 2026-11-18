# -*- coding: utf-8 -*-
"""데빌즈 서드(Wii U, 일본판) 한글 패치 적용기 — 가지고 있는 일본판 게임 파일로 한글판 파일을 만든다.

  패치하기.bat 에 게임 폴더를 끌어다 놓거나, 실행한 뒤 경로를 입력한다.
  python patch.py <게임 폴더(content 가 들어 있는 폴더) 또는 content 폴더>

결과(원본 파일은 바뀌지 않는다):
  출력/sdcafiine/0005000010138F00/DevilsThirdKR/content/...   Wii U 실기(SDCafiine)용
  출력/cemu/DevilsThirdKR/                                     Cemu 그래픽팩용(같은 파일을 하드 링크로)

패치 데이터에는 원본 게임 데이터를 넣지 않는다. 파일마다 바뀐 부분(xdelta)만 담고, 압축·암호는 여기서 다시 한다.
  full      통째 압축 패키지: 풀어서 xdelta → zlib 6 으로 다시 압축
  chunked   청크 압축 패키지: 몸통을 풀어서 xdelta → 빌드본과 같은 청크 경계로 다시 압축
  coalesced 암호화된 문자열 묶음: 복호화해서 xdelta → 다시 암호화
  raw       그대로 xdelta
  copy      작은 파일(풀린 크기 숫자)은 그대로 담음
모든 결과는 기준 해시(SHA-1)와 대조한다.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'lib'))
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402

PAYLOAD = os.path.join(HERE, 'payload')
XDELTA = os.path.join(HERE, 'bin', 'xdelta3.exe')
OUT = os.path.join(TOP, '출력')
TID = '0005000010138F00'
MOD = 'DevilsThirdKR'


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def find_content(arg):
    """게임 폴더·content·DevilsThirdGame·CookedWiiU 어느 것을 줘도 content 폴더를 찾는다."""
    arg = os.path.abspath(arg.strip().strip('"'))
    for cand in (arg, os.path.join(arg, 'content'), os.path.dirname(arg), os.path.dirname(os.path.dirname(arg))):
        if os.path.isfile(os.path.join(cand, 'DevilsThirdGame', 'CookedWiiU', 'Coalesced_JPN.bin')):
            return cand
    return None


def xdelta_apply(src, delta, tmp):
    a, d, o = (os.path.join(tmp, n) for n in ('src', 'delta', 'out'))
    open(a, 'wb').write(src)
    open(d, 'wb').write(delta)
    if os.path.exists(o):
        os.remove(o)
    r = subprocess.run([XDELTA, '-d', '-f', '-s', a, d, o], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError('xdelta3 실패: %s' % r.stderr.decode('utf-8', 'replace'))
    return open(o, 'rb').read()


def rechunk(body, hdr, chunks):
    """청크 압축 패키지 다시 묶기: 머리(빌드본 그대로) + 청크마다 zlib 6. ue3pkg.repack 의 끝부분과 같은 계산."""
    blobs = [ue3full.pack(bytes(body[s:s + n]), 6, pad=False) for s, n in chunks]
    out = bytes(hdr) + b''.join(blobs)
    return out + b'\0' * (-len(out) % 0x8000)


def make(entry, orig, tmp):
    kind = entry['kind']
    delta = open(os.path.join(PAYLOAD, entry['data']), 'rb').read()
    if kind == 'copy':
        return delta
    if kind == 'raw':
        return xdelta_apply(orig, delta, tmp)
    if kind == 'full':
        return ue3full.pack(xdelta_apply(ue3full.unpack(orig), delta, tmp), 6)
    if kind == 'chunked':
        body = xdelta_apply(ue3pkg.Pkg(orig).unpacked(), delta, tmp)
        hdr = open(os.path.join(PAYLOAD, entry['header']), 'rb').read()
        return rechunk(body, hdr, entry['chunks'])
    if kind == 'coalesced':
        from Crypto.Cipher import AES
        key = bytes.fromhex(entry['key'])
        plain = xdelta_apply(AES.new(key, AES.MODE_ECB).decrypt(orig), delta, tmp)
        plain += b'\0' * (-len(plain) % 16)
        return AES.new(key, AES.MODE_ECB).encrypt(plain)
    raise ValueError(kind)


def link_or_copy(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def main():
    man = json.load(open(os.path.join(PAYLOAD, 'manifest.json'), encoding='utf-8'))
    print('데빌즈 서드 한글 패치 %s\n' % man['version'])
    arg = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].strip() else None
    if not arg:
        print('일본판 「デビルズサード」 게임 폴더(content 폴더가 들어 있는 폴더) 경로를 입력하세요.\n'
              '폴더를 이 창에 끌어다 놓아도 됩니다.')
        arg = input('> ')
    src = find_content(arg)
    if not src:
        print('[오류] DevilsThirdGame\\CookedWiiU\\Coalesced_JPN.bin 이 있는 content 폴더를 찾지 못했습니다: %s' % arg)
        return 1
    print('원본 content 폴더: %s\n' % src)
    files = man['files']
    print('[1/3] 원본 확인')
    origs = {}
    for e in files:
        if e['kind'] == 'copy':
            continue
        p = os.path.join(src, *e['path'].split('/'))
        if not os.path.isfile(p):
            print('[오류] 원본에 %s 가 없습니다.' % e['path'])
            return 1
        b = open(p, 'rb').read()
        if len(b) != e['src_size'] or sha1(b) != e['src_sha1']:
            print('[오류] %s 가 일본판 원본과 다릅니다(이미 패치했거나 다른 판).' % e['path'])
            return 1
        origs[e['path']] = b
        print('  %-48s 일치' % e['path'])
    print('\n[2/3] 한글판 만들기')
    base = os.path.join(OUT, 'sdcafiine', TID, MOD, 'content')
    tmp = tempfile.mkdtemp(prefix='dt_ko_')
    try:
        for e in files:
            t = time.time()
            data = make(e, origs.get(e['path']), tmp)
            if sha1(data) != e['out_sha1']:
                print('[오류] %s 결과가 기준과 다릅니다. 패치 파일이 손상됐을 수 있습니다.' % e['path'])
                return 1
            dst = os.path.join(base, *e['path'].split('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'wb').write(data)
            print('  %-48s %.0f초 · 결과 확인 일치' % (e['path'], time.time() - t))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('\n[3/3] Cemu 그래픽팩')
    gp = os.path.join(OUT, 'cemu', MOD)
    os.makedirs(gp, exist_ok=True)
    shutil.copyfile(os.path.join(HERE, 'rules.txt'), os.path.join(gp, 'rules.txt'))
    for e in files:
        dst = os.path.join(gp, 'content', *e['path'].split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        link_or_copy(os.path.join(base, *e['path'].split('/')), dst)
    print('  %s' % gp)
    print('\n완료.\n  Wii U(SDCafiine): 출력\\sdcafiine 폴더 안의 내용을 SD 카드 wiiu\\sdcafiine\\ 에 복사합니다.'
          '\n  Cemu: 출력\\cemu\\%s 폴더를 Cemu 의 graphicPacks 폴더에 넣고 그래픽팩에서 켭니다.' % MOD)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n중단했습니다.')
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        print('[오류] 예상하지 못한 문제가 생겼습니다.')
        sys.exit(1)
