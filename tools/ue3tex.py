"""UE3 Texture2D(Wii U, DXT5) 꺼내기·바꾸기.

Texture2D 익스포트 = NetIndex(u32) + 프로퍼티(… None) + 네이티브:
  SourceArt 벌크 머리(16) + mip 수(u32) + mip마다 [벌크 머리 16바이트(flags, 개수, 디스크 크기, 파일 위치) + 데이터 + SizeX + SizeY] + …
Wii U 데이터는 GX2 tileMode 4 로 스위즐됨(gtx_lib.tm4, 16바이트 블록).
"""
import struct
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gtx_lib  # noqa: E402


def find_mip(exp_bytes, w, h, bpb=16):
    """첫 mip 데이터 위치를 찾는다: 벌크 머리의 디스크 크기가 w*h(블록 기준 바이트)인 곳."""
    size = (w // 4) * (h // 4) * bpb
    key = struct.pack('>II', size, size)
    i = exp_bytes.find(key)
    while i != -1:
        # flags(4) count(4) sizeOnDisk(4) offset(4) — count == size, sizeOnDisk == size
        off = i + 12
        if off + size <= len(exp_bytes):
            return off, size
        i = exp_bytes.find(key, i + 1)
    raise ValueError('mip 못 찾음')


def bc3_decode(blocks):
    """blocks: (rows, cols, 16) uint8 → RGBA (rows*4, cols*4, 4)"""
    rows, cols, _ = blocks.shape
    b = blocks.reshape(-1, 16).astype(np.uint32)
    # 알파
    a0, a1 = b[:, 0], b[:, 1]
    abits = np.zeros(len(b), np.uint64)
    for k in range(6):
        abits |= b[:, 2 + k].astype(np.uint64) << np.uint64(8 * k)
    pal = np.zeros((len(b), 8), np.uint32)
    pal[:, 0], pal[:, 1] = a0, a1
    big = a0 > a1
    for k in range(1, 7):
        pal[:, k + 1] = np.where(big, ((7 - k) * a0 + k * a1) // 7, 0)
    for k in range(1, 5):
        pal[:, k + 1] = np.where(big, pal[:, k + 1], ((5 - k) * a0 + k * a1) // 5)
    pal[:, 6] = np.where(big, pal[:, 6], 0)
    pal[:, 7] = np.where(big, pal[:, 7], 255)
    aidx = np.stack([(abits >> np.uint64(3 * i)) & np.uint64(7) for i in range(16)], 1).astype(np.int64)
    alpha = np.take_along_axis(pal, aidx, 1)
    # 색
    c0 = b[:, 8] | (b[:, 9] << 8)
    c1 = b[:, 10] | (b[:, 11] << 8)

    def rgb(c):
        return np.stack([((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31], 1)
    p0, p1 = rgb(c0), rgb(c1)
    cp = np.stack([p0, p1, (2 * p0 + p1) // 3, (p0 + 2 * p1) // 3], 1)
    cbits = b[:, 12] | (b[:, 13] << 8) | (b[:, 14] << 16) | (b[:, 15] << 24)
    cidx = np.stack([(cbits >> (2 * i)) & 3 for i in range(16)], 1).astype(np.int64)
    col = np.take_along_axis(cp, cidx[:, :, None].repeat(3, 2), 1)
    rgba = np.concatenate([col, alpha[:, :, None]], 2).astype(np.uint8)
    rgba = rgba.reshape(rows, cols, 4, 4, 4).transpose(0, 2, 1, 3, 4).reshape(rows * 4, cols * 4, 4)
    return rgba


def decode_page(exp_bytes, w, h):
    off, size = find_mip(exp_bytes, w, h)
    raw = exp_bytes[off:off + size]
    lin = gtx_lib.deswizzle(raw, w // 4, 16)
    return bc3_decode(lin), off, size
