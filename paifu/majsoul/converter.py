import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..common import WIND_KEYS, WINDS, PaifuError, fail, load_json_input, sort_tiles, tile_kind
from ..jsonfmt import write_json
from ..paifu import Paifu
from ..round_replay import RoundReplay
from .proto import decode_game_record
from .rules import MAJSOUL_STD

RULE = MAJSOUL_STD.name
LIVE_AND_DEAD_WALL = 83

# OptionalOperation.type values that answer another player's discard or kan.
CALL_OPERATIONS = {2: "chi", 3: "pon", 5: "open_kan", 9: "ron"}
# RecordLiuJu.type values.
LIUJU_TYPES = {1: "nine_terminals", 2: "four_winds", 3: "four_kans", 4: "four_riichi", 5: "three_ron"}
# RecordAnGangAddGang.type values.
ANGANG = 3
ADDGANG = 2
# RecordChiPengGang.type values.
CHIPENGGANG_TYPES = {0: "chi", 1: "pon", 2: "open_kan"}
DRAW_RECORDS = (".lq.RecordNoTile", ".lq.RecordLiuJu")
PASS = {"type": "pass"}
DRAW = {"type": "draw"}


def parse_paipu_link(link):
    """Split a Mahjong Soul record link (or bare paipu ID) into the parts described in majsoul_std.md."""
    query = parse_qs(urlparse(link).query)
    paipu_id = query["paipu"][0] if "paipu" in query else link.strip()
    record_uuid, _, account_suffix = paipu_id.partition("_")
    if not record_uuid or "-" not in record_uuid:
        fail(f"not a Mahjong Soul paipu link or ID: {link!r}")
    return {
        "paipu_id": paipu_id,
        "record_uuid": record_uuid,
        "account_suffix": account_suffix or None,
        "date_prefix": record_uuid.split("-", 1)[0],
    }


def convert(source, verify=True):
    """Convert a Mahjong Soul record into a validated Paifu.

    `source` is a dumped record ({"head": ..., "data": base64}), a decoded record ({"actions": [...]}),
    or a path / JSON text of either. With `verify`, the replay is cross-checked against the record's
    draws, call options, dora reveals and score changes, and any disagreement raises PaifuError.
    """
    record = load_json_input(source) if not isinstance(source, dict) else source
    if "actions" not in record:
        record = decode_game_record(record)
    uuid = record.get("uuid") or "record"
    rounds = []
    builder = None
    actions = record["actions"]
    try:
        for i, action in enumerate(actions):
            name, data = action["name"], action["data"]
            if name == ".lq.RecordNewRound":
                if builder is not None:
                    rounds.append(builder.finish())
                builder = _RoundBuilder(data, len(rounds), verify)
                continue
            if builder is None:
                fail(f"{name} appears before the first RecordNewRound")
            following = actions[i + 1]["name"] if i + 1 < len(actions) else None
            builder.feed(name, data, following)
        if builder is None:
            fail("the record has no rounds")
        rounds.append(builder.finish())
    except PaifuError as error:
        raise PaifuError(f"{uuid}: {error}") from error
    return Paifu({"rule": RULE, "rounds": rounds})


def convert_file(src, dst, verify=True):
    paifu = convert(json.loads(Path(src).read_text(encoding="utf-8")), verify)
    write_json(dst, paifu)
    return paifu


class _RoundBuilder:
    """Translates one round of Mahjong Soul records while replaying it, so passes and tile sources follow the Paifu rules."""

    def __init__(self, data, index, verify):
        self.verify = verify
        self.index = index
        self.dealer = data.get("ju", 0) % 4
        chang, ju = data.get("chang", 0), data.get("ju", 0)
        if chang > 3 or ju > 3:
            fail(f"unsupported round chang={chang} ju={ju}")
        scores = data.get("scores", [])
        if len(scores) != 4:
            fail("only four-player records are supported")
        metainfo = {
            "wind": WINDS[chang],
            "round": ju + 1,
            "honba": data.get("ben", 0),
            "kyotaku": data.get("liqibang", 0),
            "scores": {WIND_KEYS[self.wind(seat)]: scores[seat] for seat in self._seats()},
        }
        hands = {WIND_KEYS[self.wind(seat)]: sort_tiles(data.get(f"tiles{seat}", [])) for seat in self._seats()}
        self.data = {
            "metainfo": metainfo,
            "tiles": {"initial_hands": hands, **_split_paishan(data.get("paishan", ""))},
            "decisions": [],
        }
        self.decisions = self.data["decisions"]
        self.ended_by_record = False
        self.replay = RoundReplay(self.data, MAJSOUL_STD, index)
        self.replay.next_snapshot()
        if verify and "doras" in data:
            self._check_doras(data["doras"])

    def _seats(self):
        return [(self.dealer + i) % 4 for i in range(4)]

    def wind(self, seat):
        return (seat - self.dealer) % 4

    def _fail(self, message):
        meta = self.data["metainfo"]
        fail(f"round {self.index + 1} ({meta['wind']}{meta['round']}, honba {meta['honba']}), decision {len(self.decisions)}: {message}")

    def _push(self, decision, then_draw=False):
        self.decisions.append(decision)
        if then_draw:
            self.decisions.append(DRAW)
        self.replay.next_snapshot()

    def _expect_player(self, seat):
        if self.replay.phase != "self" or self.replay.current != self.wind(seat):
            self._fail(f"seat {seat} acts, but the replay expects {WINDS[self.replay.current]} in phase {self.replay.phase}")

    def _pass_if_pending(self):
        if self.replay.phase == "call":
            self._push(PASS)

    def feed(self, name, data, following):
        handler = {
            ".lq.RecordDealTile": self._deal,
            ".lq.RecordDiscardTile": self._discard,
            ".lq.RecordChiPengGang": self._chi_peng_gang,
            ".lq.RecordAnGangAddGang": self._an_gang_add_gang,
            ".lq.RecordHule": self._hule,
            ".lq.RecordNoTile": self._no_tile,
            ".lq.RecordLiuJu": self._liu_ju,
        }.get(name)
        if handler is None:
            self._fail(f"unsupported record {name}")
        if self.ended_by_record:
            self._fail(f"{name} follows the end of the round")
        self.ended_by_record = name in DRAW_RECORDS or name == ".lq.RecordHule"
        handler(data, following)

    def _deal(self, data, following):
        self._pass_if_pending()
        latest = self.replay.latest or {}
        if latest.get("type") not in ("deal", "replacement") or latest.get("player") != WINDS[self.wind(data["seat"])]:
            self._fail(f"the record draws for seat {data['seat']}, but the replay is at {latest}")
        if self.verify:
            if latest["tile"] != data["tile"]:
                self._fail(f"seat {data['seat']} draws {data['tile']}, but the replay draws {latest['tile']}")
            if "doras" in data:
                self._check_doras(data["doras"])

    def _discard(self, data, following):
        seat, tile = data["seat"], data["tile"]
        self._expect_player(seat)
        drawn = self.replay.drawn
        source = "deal" if data.get("moqie") and drawn is not None else "hand"
        if self.verify and data.get("moqie") and drawn != tile:
            self._fail(f"seat {seat} discards {tile} as moqie, but the drawn tile is {drawn}")
        decision_type = "riichi_declaration" if data.get("is_liqi") or data.get("is_wliqi") else "discard"
        self._push({"type": decision_type, "tile": tile, "from": source}, then_draw=following in DRAW_RECORDS)
        if self.verify:
            self._check_call_options(data.get("operations", []), f"the discard of {tile}")
            if "doras" in data:
                self._check_doras(data["doras"])

    def _chi_peng_gang(self, data, following):
        seat = data["seat"]
        tiles, froms = data["tiles"], data["froms"]
        own = [t for t, f in zip(tiles, froms) if f == seat]
        called = [t for t, f in zip(tiles, froms) if f != seat]
        if len(called) != 1:
            self._fail(f"a call must take exactly one tile from another player: {tiles} {froms}")
        kinds = {tile_kind(t) for t in tiles}
        decision_type = "chi" if len(kinds) == 3 else "pon" if len(tiles) == 3 else "open_kan"
        if self.verify and CHIPENGGANG_TYPES.get(data.get("type", 0)) != decision_type:
            self._fail(f"RecordChiPengGang.type {data.get('type', 0)} does not match the {decision_type} shape {tiles}")
        if self.replay.phase != "call":
            self._fail(f"{decision_type} by seat {seat} without a pending call_decision")
        self._push({"type": decision_type, "player": WINDS[self.wind(seat)], "hands": sort_tiles(own), "tile": called[0]})

    def _an_gang_add_gang(self, data, following):
        seat = data["seat"]
        self._expect_player(seat)
        kind = tile_kind(data["tiles"])
        hand = self.replay.hands[self.wind(seat)]
        same = sort_tiles(t for t in hand if tile_kind(t) == kind)
        kan_type = data.get("type")
        if kan_type == ANGANG:
            if len(same) != 4:
                self._fail(f"seat {seat} declares a closed kan of {data['tiles']} holding {same}")
            self._push({"type": "closed_kan", "hands": same})
        elif kan_type == ADDGANG:
            if len(same) != 1:
                self._fail(f"seat {seat} declares an added kan of {data['tiles']} holding {same}")
            self._push({"type": "added_kan", "hands": same})
        else:
            self._fail(f"unknown RecordAnGangAddGang.type {kan_type}")
        if self.verify:
            self._check_call_options(data.get("operations", []), f"the kan of {data['tiles']}")

    def _hule(self, data, following):
        hules = data["hules"]
        if all(h.get("zimo") for h in hules):
            if len(hules) != 1:
                self._fail("a tsumo must have exactly one winner")
            self._expect_player(hules[0]["seat"])
            self._push({"type": "tsumo"})
        else:
            if self.replay.phase != "call":
                self._fail("ron without a pending call_decision")
            self._push({"type": "ron", "players": [WINDS[self.wind(h["seat"])] for h in hules]})
        if self.verify:
            self._check_deltas(data.get("delta_scores", []))

    def _end_in_draw(self):
        replay = self.replay
        if replay.finished:
            return
        if replay.phase == "call":
            if replay.ptr < len(self.decisions):
                self.decisions.insert(replay.ptr, PASS)
                replay.next_snapshot()
            else:
                self._push(PASS, then_draw=True)
        elif replay.ptr < len(self.decisions):
            replay.next_snapshot()
        else:
            self._push(DRAW)
        if not replay.finished:
            self._fail("the record ends the round in a draw, but the replay does not")

    def _no_tile(self, data, following):
        self._end_in_draw()
        if not self.verify:
            return
        latest = self.replay.latest
        if latest["draw_type"] != "exhaustive":
            self._fail(f"the record has an exhaustive draw, but the replay ends in {latest['draw_type']}")
        players = data.get("players", [])
        ready = [WINDS[self.wind(seat)] for seat, p in enumerate(players) if p.get("tingpai")]
        ready = [w for w in WINDS if w in ready]
        if ready != latest["ready_players"]:
            self._fail(f"ready players are {ready} in the record, but {latest['ready_players']} in the replay")
        deltas = [0] * 4
        for score in data.get("scores", []):
            for seat, delta in enumerate(score.get("delta_scores", [])):
                deltas[seat] += delta
        self._check_deltas(deltas)

    def _liu_ju(self, data, following):
        self._end_in_draw()
        if self.verify:
            expected = LIUJU_TYPES.get(data.get("type"))
            actual = self.replay.latest["draw_type"]
            if expected != actual:
                self._fail(f"the record has an abortive draw {expected}, but the replay ends in {actual}")

    def _check_call_options(self, operations, what):
        expected = {}
        for item in operations:
            names = {CALL_OPERATIONS[op["type"]] for op in item.get("operation_list", []) if op.get("type") in CALL_OPERATIONS}
            if names:
                expected[WINDS[self.wind(item["seat"])]] = names
        actual = {WINDS[p]: set(options) for p, options in self.replay.options.items()}
        if expected != actual:
            self._fail(f"call options after {what} are {_fmt(expected)} in the record, but {_fmt(actual)} in the replay")

    def _check_doras(self, doras):
        replay = self.replay
        revealed = list(replay.dora_all[:replay.dora_revealed])
        if list(doras) != revealed:
            self._fail(f"dora indicators are {doras} in the record, but {revealed} in the replay")

    def _check_deltas(self, record_deltas):
        if not record_deltas:
            return
        summary = self.replay.summary
        if summary is None:
            self._fail("the round has not been settled by the replay")
        replay_deltas = {seat: summary["deltas"][self.wind(seat)] for seat in range(4)}
        expected = dict(enumerate(record_deltas))
        if expected != replay_deltas:
            self._fail(f"score changes by seat are {record_deltas} in the record, but {[replay_deltas[s] for s in range(4)]} in the replay")

    def finish(self):
        if not (self.replay.finished and self.ended_by_record):
            self._fail("the record and the replay disagree on where the round ends")
        return self.data


def _split_paishan(paishan):
    tiles = [paishan[i:i + 2] for i in range(0, len(paishan), 2)]
    if len(tiles) < LIVE_AND_DEAD_WALL:
        fail(f"RecordNewRound.paishan has {len(tiles)} tiles, expected 136 or 83")
    tiles = tiles[-LIVE_AND_DEAD_WALL:]
    dead = tiles[MAJSOUL_STD.wall_size:]
    return {
        "wall": tiles[:MAJSOUL_STD.wall_size],
        "rinshan": [dead[13], dead[12], dead[11], dead[10]],
        "dora_indicators": [dead[9], dead[7], dead[5], dead[3], dead[1]],
        "ura_indicators": [dead[8], dead[6], dead[4], dead[2], dead[0]],
    }


def _fmt(options):
    return {k: sorted(v) for k, v in sorted(options.items())}
