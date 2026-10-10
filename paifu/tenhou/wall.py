"""Reproduce Tenhou's walls from the SHUFFLE seed of a mjlog (mt19937ar-sha512-n288-base64)."""
import base64
import hashlib
import struct

from ..common import fail

SEED_PREFIX = "mt19937ar-sha512-n288-base64,"
TILE_COUNT = 136


class _MT19937:
    """Plain MT19937 seeded with init_by_array, as in the reference mt19937ar.c."""

    def __init__(self, key):
        mt = [0] * 624
        mt[0] = 19650218
        for i in range(1, 624):
            mt[i] = (1812433253 * (mt[i - 1] ^ (mt[i - 1] >> 30)) + i) & 0xFFFFFFFF
        i, j = 1, 0
        for _ in range(max(624, len(key))):
            mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1664525)) + key[j] + j) & 0xFFFFFFFF
            i, j = i + 1, j + 1
            if i >= 624:
                mt[0], i = mt[623], 1
            if j >= len(key):
                j = 0
        for _ in range(623):
            mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1566083941)) - i) & 0xFFFFFFFF
            i += 1
            if i >= 624:
                mt[0], i = mt[623], 1
        mt[0] = 0x80000000
        self.mt = mt
        self.index = 624

    def next(self):
        mt = self.mt
        if self.index >= 624:
            for k in range(624):
                y = (mt[k] & 0x80000000) | (mt[(k + 1) % 624] & 0x7FFFFFFF)
                mt[k] = mt[(k + 397) % 624] ^ (y >> 1) ^ (0x9908B0DF if y & 1 else 0)
            self.index = 0
        y = mt[self.index]
        self.index += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        return y ^ (y >> 18)


def walls(seed):
    """Yield (yama, dice) for each round of the game in order.

    yama is a permutation of Tenhou tile numbers 0-135; dice are the two values 0-5 written in INIT.seed[3:5].
    """
    if not seed.startswith(SEED_PREFIX):
        fail(f"unsupported SHUFFLE seed: {seed[:40]!r}")
    raw = base64.b64decode(seed[len(SEED_PREFIX):])
    if len(raw) != 624 * 4:
        fail(f"SHUFFLE seed has {len(raw)} bytes, expected {624 * 4}")
    mt = _MT19937(struct.unpack("<624I", raw))
    while True:
        src = [mt.next() for _ in range(288)]
        rnd = []
        for i in range(9):
            digest = hashlib.sha512(struct.pack("<32I", *src[i * 32:(i + 1) * 32])).digest()
            rnd += struct.unpack("<16I", digest)
        yama = list(range(TILE_COUNT))
        for i in range(TILE_COUNT):
            j = i + rnd[i] % (TILE_COUNT - i)
            yama[i], yama[j] = yama[j], yama[i]
        yield yama, (rnd[135] % 6, rnd[136] % 6)
