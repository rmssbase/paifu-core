import copy
from collections import Counter

from .common import (
    WIND_KEYS,
    WINDS,
    check,
    expect_dict,
    expect_int,
    expect_keys,
    expect_list,
    expect_scores,
    expect_tile,
    expect_tiles,
    expect_wind,
    expect_winds,
    fail,
    full_tile_counter,
    load_json_input,
    tile_kind,
)
from .round_replay import RoundReplay
from .rules import RULES

PAIFU_ORDER = ("rule", "rounds")
ROUND_ORDER = ("metainfo", "tiles", "decisions")
METAINFO_ORDER = ("wind", "round", "honba", "kyotaku", "scores")
TILES_ORDER = ("initial_hands", "wall", "rinshan", "dora_indicators", "ura_indicators")
DECISION_FIELDS = {
    "discard": ("type", "tile", "from"),
    "riichi_declaration": ("type", "tile", "from"),
    "chi": ("type", "player", "hands", "tile"),
    "pon": ("type", "player", "hands", "tile"),
    "open_kan": ("type", "player", "hands", "tile"),
    "closed_kan": ("type", "hands"),
    "added_kan": ("type", "hands"),
    "ron": ("type", "players"),
    "tsumo": ("type",),
    "pass": ("type",),
    "draw": ("type",),
}
HANDS_SIZE = {"chi": 2, "pon": 2, "open_kan": 3, "closed_kan": 4, "added_kan": 1}
END_DECISIONS = ("tsumo", "ron", "draw")


class Paifu:
    """A validated Paifu (a rule plus one or more rounds) with a step-by-step Snapshot replayer."""

    def __init__(self, data=None):
        self._rule = None
        self._rounds = []
        self._replays = []
        self._cursor = 0
        if data is not None:
            self.Init(data)

    def Init(self, data):
        obj = load_json_input(data)
        expect_keys(obj, "Paifu", PAIFU_ORDER)
        rule = obj["rule"]
        check(rule in RULES, f"Paifu.rule is not supported: {rule!r}")
        rules = RULES[rule]
        expect_list(obj["rounds"], "Paifu.rounds")
        check(obj["rounds"], "Paifu.rounds must not be empty")
        rounds = [_validate_round(raw, f"Paifu.rounds[{i}]", rules) for i, raw in enumerate(obj["rounds"])]
        replays = [RoundReplay(r, rules, i) for i, r in enumerate(rounds)]
        _verify_replays(replays)
        self._rule, self._rounds, self._replays = rule, rounds, replays
        self.Reset()
        return self

    def Dump(self):
        self._check_initialized()
        return {"rule": self._rule, "rounds": copy.deepcopy(self._rounds)}

    def Replay(self):
        """Return the next Snapshot; continues into the next round after a final, and returns None at the end."""
        self._check_initialized()
        while self._cursor < len(self._replays):
            snapshot = self._replays[self._cursor].next_snapshot()
            if snapshot is not None:
                return snapshot
            self._cursor += 1
            if self._cursor < len(self._replays):
                self._replays[self._cursor].reset()
        return None

    def Reset(self):
        self._check_initialized()
        self._cursor = 0
        for replay in self._replays:
            replay.reset()
        return self

    def SetRound(self, wind, round, honba=None):
        """Move the replay cursor to the start of the first round matching wind/round (and honba if given)."""
        self._check_initialized()
        for i, data in enumerate(self._rounds):
            meta = data["metainfo"]
            if meta["wind"] == wind and meta["round"] == round and (honba is None or meta["honba"] == honba):
                self._cursor = i
                self._replays[i].reset()
                return self
        suffix = "" if honba is None else f" honba {honba}"
        fail(f"Paifu has no round {wind}{round}{suffix}")

    def _check_initialized(self):
        check(self._rounds, "Paifu is not initialized")

    def __len__(self):
        return len(self._rounds)

    def __repr__(self):
        if not self._rounds:
            return "Paifu()"
        names = [f"{r['metainfo']['wind']}{r['metainfo']['round']}-{r['metainfo']['honba']}" for r in self._rounds]
        return f"Paifu(rule={self._rule!r}, rounds=[{', '.join(names)}])"


def _validate_round(obj, path, rules):
    expect_keys(obj, path, ROUND_ORDER)
    return {
        "metainfo": _validate_metainfo(obj["metainfo"], f"{path}.metainfo", rules),
        "tiles": _validate_tiles(obj["tiles"], f"{path}.tiles", rules),
        "decisions": _validate_decisions(obj["decisions"], f"{path}.decisions"),
    }


def _validate_metainfo(meta, path, rules):
    expect_keys(meta, path, METAINFO_ORDER)
    expect_wind(meta["wind"], f"{path}.wind")
    expect_int(meta["round"], f"{path}.round", 1, 4)
    expect_int(meta["honba"], f"{path}.honba", 0)
    expect_int(meta["kyotaku"], f"{path}.kyotaku", 0)
    scores = expect_scores(meta["scores"], f"{path}.scores")
    total = sum(scores.values()) + meta["kyotaku"] * 1000
    check(total == rules.total_points, f"{path}: scores plus kyotaku add up to {total}, expected {rules.total_points}")
    result = {key: meta[key] for key in METAINFO_ORDER}
    result["scores"] = scores
    return result


def _validate_tiles(tiles, path, rules):
    expect_keys(tiles, path, TILES_ORDER)
    hands = tiles["initial_hands"]
    expect_keys(hands, f"{path}.initial_hands", WIND_KEYS)
    for i, key in enumerate(WIND_KEYS):
        hand = expect_tiles(hands[key], f"{path}.initial_hands.{key}", sorted_required=True)
        expected = 14 if i == 0 else 13
        check(len(hand) == expected, f"{path}.initial_hands.{key} must have {expected} tiles")
    sizes = {
        "wall": rules.wall_size,
        "rinshan": rules.rinshan_size,
        "dora_indicators": rules.indicator_size,
        "ura_indicators": rules.indicator_size,
    }
    for key, size in sizes.items():
        expect_tiles(tiles[key], f"{path}.{key}")
        check(len(tiles[key]) == size, f"{path}.{key} must have {size} tiles, got {len(tiles[key])}")
    counter = Counter()
    for key in WIND_KEYS:
        counter.update(hands[key])
    for key in sizes:
        counter.update(tiles[key])
    full = full_tile_counter()
    if counter != full:
        diff = []
        for tile in sorted(set(counter) | set(full)):
            if counter[tile] != full[tile]:
                diff.append(f"{tile} {counter[tile]}/{full[tile]}")
        fail(f"{path} is not a complete tile set (count/expected): {', '.join(diff)}")
    result = {"initial_hands": {key: list(hands[key]) for key in WIND_KEYS}}
    for key in sizes:
        result[key] = list(tiles[key])
    return result


def _validate_decisions(decisions, path):
    expect_list(decisions, path)
    check(decisions, f"{path} must not be empty")
    result = []
    for i, decision in enumerate(decisions):
        item = f"{path}[{i}]"
        expect_dict(decision, item)
        decision_type = decision.get("type")
        check(decision_type in DECISION_FIELDS, f"{item}.type is invalid: {decision_type!r}")
        fields = DECISION_FIELDS[decision_type]
        expect_keys(decision, item, fields)
        if "tile" in decision:
            expect_tile(decision["tile"], f"{item}.tile")
        if "from" in decision:
            check(decision["from"] in ("hand", "deal"), f"{item}.from must be hand or deal")
        if "player" in decision:
            expect_wind(decision["player"], f"{item}.player")
        if "players" in decision:
            expect_winds(decision["players"], f"{item}.players", allow_empty=False)
        if "hands" in decision:
            hands = expect_tiles(decision["hands"], f"{item}.hands", sorted_required=True)
            size = HANDS_SIZE[decision_type]
            check(len(hands) == size, f"{item}.hands must have {size} tiles")
            if decision_type == "closed_kan":
                check(len({tile_kind(t) for t in hands}) == 1, f"{item}.hands must be four tiles of one kind")
        result.append({key: decision[key] for key in fields})
        is_end = decision_type in END_DECISIONS
        check(is_end == (i == len(decisions) - 1), f"{path} must end with exactly one tsumo, ron or draw")
    return result


def _verify_replays(replays):
    previous = None
    for replay in replays:
        if previous is not None:
            _check_continuity(previous[0], previous[1], replay)
        final = None
        while True:
            snapshot = replay.next_snapshot()
            if snapshot is None:
                break
            final = snapshot
        previous = (replay.summary, final)
        replay.reset()


def _check_continuity(summary, final, current):
    meta = final.metainfo
    start = current.data["metainfo"]
    if summary["dealer_continues"]:
        wind, round_ = meta["wind"], meta["round"]
    elif meta["round"] == 4:
        wind, round_ = WINDS[(WINDS.index(meta["wind"]) + 1) % 4], 1
    else:
        wind, round_ = meta["wind"], meta["round"] + 1
    where = f"round {current.index + 1}"
    check(
        (start["wind"], start["round"]) == (wind, round_),
        f"{where} should be {wind}{round_}, got {start['wind']}{start['round']}",
    )
    for key in ("honba", "kyotaku"):
        check(start[key] == meta[key], f"{where} should start with {key} {meta[key]}, got {start[key]}")
    shift = 0 if summary["dealer_continues"] else 1
    scores = {key: meta["scores"][WIND_KEYS[(i + shift) % 4]] for i, key in enumerate(WIND_KEYS)}
    check(start["scores"] == scores, f"{where} should start with scores {scores} (seats rotate when the dealer changes), got {start['scores']}")
