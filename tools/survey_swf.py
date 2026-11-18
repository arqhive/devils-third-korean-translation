"""전체 패키지에서 익스포트 표를 끝까지 읽어 클래스별 개수를 내고, SwfMovie 를 모두 꺼낸다.

통째 압축 패키지는 블록을 필요한 만큼만 풀어 표를 읽고, SwfMovie 가 있으면 전체를 푼다.
출력: work/survey/exports_by_class.json, work/extract/gfx_all/<패키지>__<이름>.gfx
사용: python -I tools/survey_swf.py [프로세스 수]
"""
import collections
import json
import os
import struct
import sys
import zlib
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ue3full  # noqa: E402
import ue3pkg  # noqa: E402

ROOT = os.path.dirname(HERE)
COOKED = os.path.join(ROOT, 'Devils Third [Game] [0005000010138f00]', 'content', 'DevilsThirdGame', 'CookedWiiU')
OUTG = os.path.join(ROOT, 'work', 'extract', 'gfx_all')


def load(path):
    raw = open(path, 'rb').read()
    if struct.unpack_from('>I', raw, 4)[0] == 0x20000:
        raw = ue3full.unpack(raw)
    return raw


def one(name):
    path = os.path.join(COOKED, name)
    try:
        raw = load(path)
        pk, body, names, imps, exps = ue3pkg.tables(raw)
    except Exception as e:  # noqa: BLE001
        return name, {'!error': repr(e)}, []
    cnt = collections.Counter(e['class'] for e in exps)
    swfs = []
    for e in exps:
        if e['class'] == 'SwfMovie':
            exp = body[e['offset']:e['offset'] + e['size']]
            try:
                g = ue3pkg.get_array_prop(exp, names, 'RawData')
            except Exception:  # noqa: BLE001
                g = exp[exp.find(b'GFX'):]
            out = os.path.join(OUTG, '%s__%s.gfx' % (name.rsplit('.', 1)[0], e['name']))
            open(out, 'wb').write(g)
            swfs.append(e['name'])
    return name, dict(cnt), swfs


def main():
    os.makedirs(OUTG, exist_ok=True)
    names = sorted(n for n in os.listdir(COOKED) if n.endswith('.xxx'))
    procs = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    res = {}
    swf = {}
    with Pool(procs) as p:
        for name, cnt, swfs in p.imap_unordered(one, names, chunksize=4):
            res[name] = cnt
            if swfs:
                swf[name] = swfs
    total = collections.Counter()
    for c in res.values():
        for k, v in c.items():
            if not k.startswith('!'):
                total[k] += v
    json.dump({'per_package': res, 'total': dict(total.most_common()), 'swf': swf},
              open(os.path.join(ROOT, 'work', 'survey', 'exports_by_class.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    err = [k for k, v in res.items() if '!error' in v]
    print('packages', len(res), 'errors', len(err), 'swf packages', len(swf), 'swf', sum(map(len, swf.values())))


if __name__ == '__main__':
    main()
