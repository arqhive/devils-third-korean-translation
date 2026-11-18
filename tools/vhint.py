"""윤곽선 세로 힌팅(트루타입 IUP 방식).
1) 가로 변(같은 높이로 이어진 점들)을 찾고, 위 변·아래 변을 짝지어 가로 획(스템)으로 본다.
2) 스템의 위·아래 변 점만 픽셀 경계로 옮긴다. 두께는 반올림(최소 1px).
   글자 맨 위·바닥·받침 바닥 근처 변은 글자 전체 공통 줄(존)로.
   가로로 겹치는 위아래 스템은 원래 틈이 0.5px 이상이면 옮긴 뒤에도 1px 이상.
3) 둥근 꼭대기·비스듬한 끝(윤곽의 극점)이 존 안이면 그 점도 존 줄로.
4) 안 옮긴 점은 같은 윤곽에서 앞뒤로 옮긴 점 사이를 높이 비례로 보간(IUP). 다른 획에는 영향 없음.
가로 위치·폭은 손대지 않는다.
11/18 사용자 「포로 ㅗ 획이 기준선에 같이 붙어야 하는데 차이 남」 → 워헤이븐은 한글 힌팅이 없어 22px 에서
획 위치가 글자마다 반올림이 달라짐(983자 중 같은 높이 획 1,872곳 중 369곳 1px 갈림). 이 모듈로 그리면 154곳,
획 붙음 0, 두께 1px 넘는 변화 0. 존 범위는 워헤이븐 굵게 983자 맨 위·맨 아래 변 분포의 봉우리(글꼴 단위).
필요: pip install freetype-py
"""
from collections import Counter

import freetype
import numpy as np

# 11/19 사용자 실기 「활·홀 ㅎ 꼭지가 가로 획과 3줄 덩어리」 → 이 두 글자만 가까운 변끼리 짝지음(다른 글자는 그대로)
NEAR_PAIR = '활홀'
ZONE_RANGES = [('top', 770, 850), ('bot', 5, 40), ('bot', -85, -50)]


class OHint:
    def __init__(self, size, chars, ttf):
        self.fp = open(ttf, 'rb')
        self.face = freetype.Face(self.fp)
        self.size = size
        self.face.set_char_size(int(round(size * 64)), 0, 72, 72)
        self.s = size / self.face.units_per_EM
        self.zones = []
        if chars:
            self.make_zones(chars)

    # ---------- 윤곽 분석(글꼴 단위) ----------
    def analyze(self, ch):
        f = self.face
        f.load_char(ch, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
        o = f.glyph.outline
        pts, ends = list(o.points), list(o.contours)
        tops, bots = [], []
        contours = []
        s = 0
        for e in ends:
            idx = list(range(s, e + 1))
            contours.append(idx)
            n = len(idx)
            seen = set()
            for k in range(n):
                y0 = pts[idx[k]][1]
                if abs(pts[idx[(k - 1) % n]][1] - y0) <= 3:
                    continue
                run = [idx[k]]
                m = k + 1
                while m < k + n and abs(pts[idx[m % n]][1] - y0) <= 3:
                    run.append(idx[m % n])
                    m += 1
                if len(run) < 2:
                    continue
                xs = [pts[i][0] for i in run]
                if abs(xs[-1] - xs[0]) >= 30 and tuple(run) not in seen:
                    seen.add(tuple(run))
                    yv = sorted(pts[i][1] for i in run)[len(run) // 2]
                    (tops if xs[-1] > xs[0] else bots).append((yv, min(xs), max(xs), run))
            s = e + 1
        ext = []  # 극점(둥근 꼭대기·비스듬한 끝)
        for idx in contours:
            n = len(idx)
            for k in range(n):
                y = pts[idx[k]][1]
                yp, yn = pts[idx[k - 1]][1], pts[idx[(k + 1) % n]][1]
                if y > yp and y >= yn:
                    ext.append(('top', y, [idx[k]]))
                elif y < yp and y <= yn:
                    ext.append(('bot', y, [idx[k]]))
        singles = [('top', y, run) for y, a, b, run in tops] + [('bot', y, run) for y, a, b, run in bots] + ext
        ltops = [t for t in tops if t[2] - t[1] >= 100]
        lbots = [t for t in bots if t[2] - t[1] >= 100]
        if ch in NEAR_PAIR:
            return pts, contours, self._near_pairs(ltops, lbots), singles
        stems, used = [], set()
        for ty, ta, tb, trun in sorted(ltops, key=lambda t: -t[0]):
            best = None
            for k, (by, ba, bb, brun) in enumerate(lbots):
                if k in used or by >= ty or ty - by > 200 or min(tb, bb) - max(ta, ba) < 60:
                    continue
                if best is None or by > lbots[best][0]:
                    best = k
            if best is not None:
                used.add(best)
                by, ba, bb, brun = lbots[best]
                stems.append(dict(ty=ty, by=by, x0=max(ta, ba), x1=min(tb, bb), trun=trun, brun=brun))
        return pts, contours, stems, singles

    @staticmethod
    def _near_pairs(ltops, lbots):
        """위 변·아래 변을 가까운 것부터 짝지음(NEAR_PAIR 글자만).
        기본 짝짓기는 ㅎ 꼭지 위 끝을 가로 획 아래 끝과 한 획으로 묶어 꼭지·가로 획이 3줄 덩어리가 됨."""
        cand = []
        for ti, (ty, ta, tb, trun) in enumerate(ltops):
            for bi, (by, ba, bb, brun) in enumerate(lbots):
                if by < ty and ty - by <= 200 and min(tb, bb) - max(ta, ba) >= 60:
                    cand.append((ty - by, ti, bi))
        stems, ut, ub = [], set(), set()
        for dist, ti, bi in sorted(cand):
            if ti in ut or bi in ub:
                continue
            ty, ta, tb, trun = ltops[ti]
            by, ba, bb, brun = lbots[bi]
            ut.add(ti)
            ub.add(bi)
            stems.append(dict(ty=ty, by=by, x0=max(ta, ba), x1=min(tb, bb), trun=trun, brun=brun))
        return stems

    def make_zones(self, chars):
        top, bot = Counter(), Counter()
        for c in chars:
            _, _, st, _ = self.analyze(c)
            if st:
                top[max(d['ty'] for d in st)] += 1
                bot[min(d['by'] for d in st)] += 1
        self.zones = []
        for k, lo, hi in ZONE_RANGES:
            cnt = top if k == 'top' else bot
            ys = [y for y in cnt if lo <= y <= hi]
            n = sum(cnt[y] for y in ys)
            mean = sum(y * cnt[y] for y in ys) / n
            self.zones.append((k, lo, hi, round(mean * self.s), n))

    def zone(self, kind, y):
        for k, lo, hi, tg, n in self.zones:
            if k == kind and lo <= y <= hi:
                return tg
        return None

    # ---------- 목표 높이 정하기 ----------
    def targets(self, ch):
        pts, contours, stems, singles = self.analyze(ch)
        if ch in NEAR_PAIR:
            # 이 글자는 존·틈 맞춤 없이 획 끝마다 가까운 픽셀 경계로만(원래 글꼴 위치 그대로 반올림)
            touched = {}
            for d in stems:
                T = round(d['ty'] * self.s)
                B = min(round(d['by'] * self.s), T - 1)
                for i in d['trun']:
                    touched[i] = T
                for i in d['brun']:
                    touched[i] = B
            self.plan, self.thinned, self.gap_fixes = [], False, 0
            return contours, touched
        plan = self._plan(stems, thin=False)
        if self._glued(plan):
            # 획이 촘촘해서(를·틀 등) 반올림한 두께로는 틈이 안 남음 → 이 글자는 스템 두께를 내림(최소 1px)
            plan = self._plan(stems, thin=True)
        self.thinned = self._glued(plan) is not None
        touched = {}
        for p in plan:
            for i in p['trun']:
                touched[i] = p['T']
            for i in p['brun']:
                touched[i] = p['B']
        for kind, y, run in singles:
            z = self.zone(kind, y)
            if z is None:
                continue
            for i in run:
                touched.setdefault(i, z)
        self.plan = plan
        return contours, touched

    def _glued(self, plan):
        for i in range(len(plan)):
            for j in range(i):
                u, p = plan[j], plan[i]
                if min(u['x1'], p['x1']) - max(u['x0'], p['x0']) <= 0:
                    continue
                if p['ty'] >= u['by'] or (u['by'] - p['ty']) * self.s < 0.5:
                    continue
                if u['B'] - p['T'] < 1:
                    return (j, i)
        return None

    def _plan(self, stems, thin):
        s = self.s
        plan = []
        for d in stems:
            raw = (d['ty'] - d['by']) * s
            th = max(1, int(raw) if thin else round(raw))
            zt, zb = self.zone('top', d['ty']), self.zone('bot', d['by'])
            if zt is not None:
                T1, B1 = zt, zt - th
            elif zb is not None:
                B1, T1 = zb, zb + th
            else:
                T1 = round(d['ty'] * s)
                B1 = T1 - th
            plan.append(dict(d, T=T1, B=B1, zt=zt is not None, zb=zb is not None))
        plan.sort(key=lambda p: -p['ty'])
        self.gap_fixes = 0
        for _ in range(4):
            changed = False
            for i in range(1, len(plan)):
                for j in range(i):
                    up, dn = plan[j], plan[i]
                    if min(up['x1'], dn['x1']) - max(up['x0'], dn['x0']) <= 0:
                        continue  # 가로로 안 겹침 → 서로 상관없음
                    if dn['ty'] >= up['by'] or (up['by'] - dn['ty']) * s < 0.5:
                        continue
                    need = (dn['T'] + 1) - up['B']
                    if need <= 0:
                        continue
                    changed = True
                    self.gap_fixes += 1
                    if not dn['zb']:
                        dn['T'] -= need
                        dn['B'] -= need
                    elif not up['zt']:
                        up['T'] += need
                        up['B'] += need
                    elif up['T'] - up['B'] > 1:
                        up['B'] += need
                    elif dn['T'] - dn['B'] > 1:
                        dn['T'] -= need
            if not changed:
                break
        return plan

    # ---------- 그리기 ----------
    def render(self, ch):
        """(배열 float, 위 오프셋(px, 기준선 기준 위가 -), 왼쪽(px), 진행 폭)"""
        contours, touched = self.targets(ch)
        f = self.face
        f.load_char(ch, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP)
        g = f.glyph
        adv = g.advance.x / 64.0
        o = g.outline._FT_Outline
        y0 = [o.points[i].y / 64.0 for i in range(o.n_points)]
        y1 = list(y0)
        for idx in contours:
            tk = [i for i in idx if i in touched]
            for i in tk:
                y1[i] = float(touched[i])
            if not tk:
                continue
            if len(tk) == 1:
                dlt = y1[tk[0]] - y0[tk[0]]
                for i in idx:
                    if i not in touched:
                        y1[i] = y0[i] + dlt
                continue
            n = len(idx)
            pos = {p: k for k, p in enumerate(idx)}
            for a_i, a in enumerate(tk):
                b = tk[(a_i + 1) % len(tk)]
                k = (pos[a] + 1) % n
                while idx[k] != b:
                    p = idx[k]
                    ya, yb = y0[a], y0[b]
                    da, db = y1[a] - ya, y1[b] - yb
                    if ya == yb:
                        y1[p] = y0[p] + (da if abs(y0[p] - ya) <= 0 else (da if da == db else da))
                    else:
                        lo, hi = (a, b) if ya < yb else (b, a)
                        if y0[p] <= y0[lo]:
                            y1[p] = y0[p] + (y1[lo] - y0[lo])
                        elif y0[p] >= y0[hi]:
                            y1[p] = y0[p] + (y1[hi] - y0[hi])
                        else:
                            t = (y0[p] - y0[lo]) / (y0[hi] - y0[lo])
                            y1[p] = y1[lo] + t * (y1[hi] - y1[lo])
                    k = (k + 1) % n
        for i in range(o.n_points):
            o.points[i].y = int(round(y1[i] * 64))
        g.render(freetype.FT_RENDER_MODE_NORMAL)
        bm = g.bitmap
        if not bm.rows:
            return None, 0, 0, adv
        a = np.array(bm.buffer, np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width].astype(np.float32)
        return a, -g.bitmap_top, g.bitmap_left, adv
