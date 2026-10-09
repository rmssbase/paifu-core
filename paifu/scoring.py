from collections import Counter
from dataclasses import dataclass, field

from .common import (
    DRAGON_KINDS,
    GREEN_KINDS,
    HONOR_START,
    WIND_KINDS,
    YAOCHU_KINDS,
    dora_kind,
    is_red,
    kinds_counts,
    tile_kind,
)
from .hand import is_seven_pairs, is_thirteen_orphans, standard_decompositions

HONOR_KINDS = frozenset(range(HONOR_START, 34))
TERMINAL_KINDS = YAOCHU_KINDS - HONOR_KINDS
NINE_GATES_PATTERN = (3, 1, 1, 1, 1, 1, 1, 1, 3)


@dataclass
class WinContext:
    concealed: list
    melds: list
    win_tile: str
    tsumo: bool
    seat_wind: int
    round_wind: int
    riichi: bool = False
    double_riichi: bool = False
    ippatsu: bool = False
    rinshan: bool = False
    chankan: bool = False
    haitei: bool = False
    houtei: bool = False
    tenhou: bool = False
    chiihou: bool = False
    dora_indicators: list = field(default_factory=list)
    ura_indicators: list = field(default_factory=list)


@dataclass
class WinResult:
    yaku: list
    yakuman: list
    han: int
    fu: int
    dora: int
    aka: int
    ura: int
    base: int

    @property
    def yakuman_multiplier(self):
        return sum(multiplier for _, multiplier in self.yakuman)


def ceil100(value):
    return -(-value // 100) * 100


def base_points(han, fu, rules):
    if han >= 13 and rules.kazoe_yakuman:
        return 8000
    if han >= 11:
        return 6000
    if han >= 8:
        return 4000
    if han >= 6:
        return 3000
    if han >= 5:
        return 2000
    return min(fu * 2 ** (han + 2), 2000)


def evaluate_win(ctx, rules):
    """Return the highest scoring interpretation of a complete hand, or None when it has no yaku."""
    counts = kinds_counts(ctx.concealed)
    win_kind = tile_kind(ctx.win_tile)
    meld_groups = [_meld_group(meld) for meld in ctx.melds]
    all_tiles = list(ctx.concealed) + [tile for meld in ctx.melds for tile in meld["tiles"]]
    all_counts = kinds_counts(all_tiles)
    used = {k for k, c in enumerate(all_counts) if c}
    menzen = all(not group[2] for group in meld_groups)
    common_yakuman = _common_yakuman(ctx, counts, used, win_kind)

    candidates = []
    if not ctx.melds and is_thirteen_orphans(counts):
        rest = list(counts)
        rest[win_kind] -= 1
        name = ("thirteen_orphans_thirteen_wait", 2) if all(rest[k] == 1 for k in YAOCHU_KINDS) else ("thirteen_orphans", 1)
        candidates.append(_finish(ctx, rules, [], common_yakuman + [name], 0, all_tiles))
    if not ctx.melds and is_seven_pairs(counts):
        candidates.append(_seven_pairs(ctx, rules, used, common_yakuman, all_tiles))
    for pair, groups in standard_decompositions(counts):
        seen = set()
        for placement in _placements(pair, groups, win_kind):
            key = (placement[0], groups[placement[1]] if placement[1] is not None else None)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                _standard(ctx, rules, pair, groups, placement, meld_groups, menzen, used, win_kind, common_yakuman, all_tiles)
            )
    candidates = [c for c in candidates if c is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda r: (r.base, r.han, r.fu))


def _meld_group(meld):
    kinds = [tile_kind(tile) for tile in meld["tiles"]]
    if meld["type"] == "chi":
        return ("seq", min(kinds), True)
    if meld["type"] == "pon":
        return ("trip", kinds[0], True)
    if meld["type"] == "closed_kan":
        return ("kan", kinds[0], False)
    return ("kan", kinds[0], True)


def _placements(pair, groups, win_kind):
    if pair == win_kind:
        yield ("pair", None)
    for i, (shape, kind) in enumerate(groups):
        if shape == "trip" and kind == win_kind:
            yield ("trip", i)
        if shape == "seq" and kind <= win_kind <= kind + 2:
            yield ("seq", i)


def _common_yakuman(ctx, counts, used, win_kind):
    result = []
    if ctx.tenhou:
        result.append(("heavenly_hand", 1))
    if ctx.chiihou:
        result.append(("hand_of_earth", 1))
    if not ctx.melds:
        suits = {k // 9 for k in used if k < HONOR_START}
        if len(suits) == 1 and not used & HONOR_KINDS:
            base = suits.pop() * 9
            suit_counts = counts[base:base + 9]
            if all(c >= p for c, p in zip(suit_counts, NINE_GATES_PATTERN)):
                rest = list(suit_counts)
                rest[win_kind - base] -= 1
                if tuple(rest) == NINE_GATES_PATTERN:
                    result.append(("true_nine_gates", 2))
                else:
                    result.append(("nine_gates", 1))
    return result


def _dora_counts(ctx, all_tiles):
    counts = kinds_counts(all_tiles)
    dora = sum(counts[dora_kind(tile_kind(t))] for t in ctx.dora_indicators)
    aka = sum(1 for t in all_tiles if is_red(t))
    ura = sum(counts[dora_kind(tile_kind(t))] for t in ctx.ura_indicators) if ctx.riichi else 0
    return dora, aka, ura


def _finish(ctx, rules, yaku, yakuman, fu, all_tiles):
    if yakuman:
        if not rules.double_yakuman:
            yakuman = [(name, 1) for name, _ in yakuman]
        multiplier = sum(m for _, m in yakuman)
        return WinResult([], yakuman, 0, fu, 0, 0, 0, 8000 * multiplier)
    han = sum(h for _, h in yaku)
    if han == 0:
        return None
    dora, aka, ura = _dora_counts(ctx, all_tiles)
    han += dora + aka + ura
    return WinResult(yaku, [], han, fu, dora, aka, ura, base_points(han, fu, rules))


def _situational_yaku(ctx, menzen):
    yaku = []
    if ctx.double_riichi:
        yaku.append(("double_riichi", 2))
    elif ctx.riichi:
        yaku.append(("riichi", 1))
    if ctx.ippatsu:
        yaku.append(("one_shot", 1))
    if menzen and ctx.tsumo:
        yaku.append(("fully_concealed_self_draw", 1))
    if ctx.rinshan and ctx.tsumo:
        yaku.append(("after_a_kan", 1))
    if ctx.chankan:
        yaku.append(("robbing_a_kan", 1))
    if ctx.haitei and ctx.tsumo and not ctx.rinshan:
        yaku.append(("last_tile_draw", 1))
    if ctx.houtei and not ctx.tsumo:
        yaku.append(("last_discard", 1))
    return yaku


def _flush_yaku(used, menzen):
    suits = {k // 9 for k in used if k < HONOR_START}
    if len(suits) != 1:
        return []
    if used & HONOR_KINDS:
        return [("half_flush", 3 if menzen else 2)]
    return [("full_flush", 6 if menzen else 5)]


def _seven_pairs(ctx, rules, used, common_yakuman, all_tiles):
    yakuman = list(common_yakuman)
    if used <= HONOR_KINDS:
        yakuman.append(("all_honors", 1))
    if yakuman:
        return _finish(ctx, rules, [], yakuman, 25, all_tiles)
    yaku = _situational_yaku(ctx, True)
    yaku.append(("seven_pairs", 2))
    if not used & YAOCHU_KINDS:
        yaku.append(("all_simples", 1))
    if used <= YAOCHU_KINDS:
        yaku.append(("all_terminals_and_honors", 2))
    yaku += _flush_yaku(used, True)
    return _finish(ctx, rules, yaku, [], 25, all_tiles)


def _standard(ctx, rules, pair, groups, placement, meld_groups, menzen, used, win_kind, common_yakuman, all_tiles):
    place_type, index = placement
    concealed_groups = []
    for i, (shape, kind) in enumerate(groups):
        is_open = not ctx.tsumo and place_type == "trip" and i == index
        concealed_groups.append((shape, kind, is_open))
    all_groups = concealed_groups + meld_groups

    if place_type == "pair":
        wait = "tanki"
    elif place_type == "trip":
        wait = "shanpon"
    else:
        start = groups[index][1]
        position = win_kind - start
        if position == 1:
            wait = "kanchan"
        elif (position == 0 and start % 9 == 6) or (position == 2 and start % 9 == 0):
            wait = "penchan"
        else:
            wait = "ryanmen"

    trips = [g for g in all_groups if g[0] in ("trip", "kan")]
    seqs = [g for g in all_groups if g[0] == "seq"]
    kans = [g for g in all_groups if g[0] == "kan"]
    closed_trips = sum(1 for g in trips if not g[2])
    dragon_trips = [g for g in trips if g[1] in DRAGON_KINDS]
    wind_trips = [g for g in trips if g[1] in WIND_KINDS]

    yakuman = list(common_yakuman)
    if closed_trips == 4:
        yakuman.append(("four_closed_triplets_single_wait", 2) if wait == "tanki" else ("four_closed_triplets", 1))
    if len(dragon_trips) == 3:
        yakuman.append(("big_three_dragons", 1))
    if len(wind_trips) == 4:
        yakuman.append(("big_four_winds", 2))
    elif len(wind_trips) == 3 and pair in WIND_KINDS:
        yakuman.append(("little_four_winds", 1))
    if used <= HONOR_KINDS:
        yakuman.append(("all_honors", 1))
    if used <= GREEN_KINDS:
        yakuman.append(("all_green", 1))
    if used <= TERMINAL_KINDS:
        yakuman.append(("all_terminals", 1))
    if len(kans) == 4:
        yakuman.append(("four_kans", 1))
    if yakuman:
        return _finish(ctx, rules, [], yakuman, 0, all_tiles)

    yaku = _situational_yaku(ctx, menzen)
    if not used & YAOCHU_KINDS:
        yaku.append(("all_simples", 1))
    valued_pair = pair in DRAGON_KINDS or pair == ctx.seat_wind or pair == ctx.round_wind
    pinfu = menzen and len(seqs) == 4 and not valued_pair and wait == "ryanmen"
    if pinfu:
        yaku.append(("no_points_hand", 1))
    if menzen:
        identical = sum(c // 2 for c in Counter(g[1] for g in seqs).values())
        if identical >= 2:
            yaku.append(("twice_pure_double_sequence", 3))
        elif identical == 1:
            yaku.append(("pure_double_sequence", 1))
    for _, kind, _ in trips:
        if kind == 31:
            yaku.append(("white_dragon", 1))
        elif kind == 32:
            yaku.append(("green_dragon", 1))
        elif kind == 33:
            yaku.append(("red_dragon", 1))
        if kind == ctx.seat_wind:
            yaku.append(("seat_wind", 1))
        if kind == ctx.round_wind:
            yaku.append(("prevalent_wind", 1))
    if len(trips) == 4:
        yaku.append(("all_triplets", 2))
    if closed_trips == 3:
        yaku.append(("three_closed_triplets", 2))
    seq_starts = {g[1] for g in seqs}
    if any(n in seq_starts and n + 9 in seq_starts and n + 18 in seq_starts for n in range(7)):
        yaku.append(("three_color_sequences", 2 if menzen else 1))
    trip_kinds = {g[1] for g in trips}
    if any(n in trip_kinds and n + 9 in trip_kinds and n + 18 in trip_kinds for n in range(9)):
        yaku.append(("three_color_triplets", 2))
    if any(all(base + offset in seq_starts for offset in (0, 3, 6)) for base in (0, 9, 18)):
        yaku.append(("straight", 2 if menzen else 1))
    has_yaochu = all((g[1] % 9 in (0, 6)) if g[0] == "seq" else (g[1] in YAOCHU_KINDS) for g in all_groups)
    if has_yaochu and pair in YAOCHU_KINDS and seqs:
        if used & HONOR_KINDS:
            yaku.append(("terminal_or_honor_in_each_set", 2 if menzen else 1))
        else:
            yaku.append(("terminal_in_each_set", 3 if menzen else 2))
    if used <= YAOCHU_KINDS:
        yaku.append(("all_terminals_and_honors", 2))
    if len(kans) == 3:
        yaku.append(("three_kans", 2))
    if len(dragon_trips) == 2 and pair in DRAGON_KINDS:
        yaku.append(("little_three_dragons", 2))
    yaku += _flush_yaku(used, menzen)

    if pinfu and ctx.tsumo:
        fu = 20
    else:
        fu = 20
        if menzen and not ctx.tsumo:
            fu += 10
        if ctx.tsumo:
            fu += 2
        if wait in ("tanki", "kanchan", "penchan"):
            fu += 2
        if pair in DRAGON_KINDS:
            fu += 2
        if pair == ctx.seat_wind:
            fu += 2
        if pair == ctx.round_wind:
            fu += 2
        for shape, kind, is_open in trips:
            value = 2 if shape == "trip" else 8
            if not is_open:
                value *= 2
            if kind in YAOCHU_KINDS:
                value *= 2
            fu += value
        fu = -(-fu // 10) * 10
        if fu == 20:
            fu = 30
    return _finish(ctx, rules, yaku, [], fu, all_tiles)
