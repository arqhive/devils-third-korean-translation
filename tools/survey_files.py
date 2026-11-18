"""전체 파일 목록·형식별 표(본편·업데이트 폴더 모두).

출력: work/survey/all_files.json([폴더, 상대경로, 크기, 확장자, 머리 4바이트]), work/survey/file_types.txt
"""
import collections
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ['Devils Third [Game] [0005000010138f00]', 'Devils Third [Update] [0005000e10138f00]']


def main():
    rows = []
    for top in DIRS:
        base = os.path.join(ROOT, top)
        for d, _, fs in os.walk(base):
            for f in fs:
                p = os.path.join(d, f)
                rel = os.path.relpath(p, base).replace(os.sep, '/')
                with open(p, 'rb') as h:
                    magic = h.read(4)
                ext = f.rsplit('.', 1)[-1].lower() if '.' in f else '(none)'
                rows.append([top, rel, os.path.getsize(p), ext, magic.hex()])
    json.dump(rows, open(os.path.join(ROOT, 'work', 'survey', 'all_files.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    c = collections.Counter()
    sz = collections.Counter()
    ex = {}
    for top, rel, s, ext, m in rows:
        k = ('Game' if 'Game' in top else 'Update', rel.split('/')[0], rel.split('/')[1] if rel.count('/') > 1 else '', ext, m)
        c[k] += 1
        sz[k] += s
        ex.setdefault(k, rel)
    with open(os.path.join(ROOT, 'work', 'survey', 'file_types.txt'), 'w', encoding='utf-8') as f:
        f.write('total %d files\n' % len(rows))
        for k, v in sorted(c.items()):
            f.write('\t'.join(map(str, k)) + '\t%d\t%d\t%s\n' % (v, sz[k], ex[k]))


if __name__ == '__main__':
    main()
