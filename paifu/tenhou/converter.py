from itertools import islice

from ..common import WIND_KEYS, WINDS, PaifuError, fail, sort_tiles
from ..jsonfmt import write_json
from ..paifu import Paifu
from ..round_replay import RoundReplay
from .mjlog import (
    GO_HANCHAN,
    GO_NO_AKA,
    GO_NO_KUITAN,
    GO_SANMA,
    decode_meld,
    load_mjlog,
    tile_list,
    tile_name,
)
from .rules import TENHOU_STD
from .wall import walls

RULE = TENHOU_STD.name
DRAW_TAGS = "TUVW"
DISCARD_TAGS = "DEFG"
# Tags that carry no game action.
IGNORED_TAGS = {"SHUFFLE", "GO", "UN", "TAIKYOKU", "BYE"}
# Tags that may sit between a discard and the record that ends the round.
TRANSPARENT_TAGS = IGNORED_TAGS | {"REACH", "DORA"}
# RYUUKYOKU.type values; a missing type is an exhaustive draw.
RYUUKYOKU_TYPES = {
    None: "exhaustive",
    "nm": "exhaustive",
    "yao9": "nine_terminals",
    "kaze4": "four_winds",
    "reach4": "four_riichi",
    "kan4": "four_kans",
    "ron3": "three_ron",
}
PASS = {"type": "pass"}
DRAW = {"type": "draw"}
# Dead wall positions in yama, in the order Paifu consumes them.
RINSHAN_POSITIONS = (1, 0, 3, 2)
DORA_POSITIONS = (5, 7, 9, 11, 13)
URA_POSITIONS = (4, 6, 8, 10, 12)


def convert(source, verify=True):
    """Convert a Tenhou mjlog into a validated Paifu.

    `source` is the mjlog XML (text or bytes), a path to it, or a parsed Element; use fetch_log to download one.
    With `verify`, the replay is cross-checked against the log's draws, dora reveals, riichi, score changes,
    draw types and final scores, and any disagreement raises PaifuError.
    """
    root = load_mjlog(source)
    events = list(root)
    try:
        _check_game_type(root)
        shuffle = root.find("SHUFFLE")
        if shuffle is None:
            fail("the mjlog has no SHUFFLE seed, so the walls cannot be reproduced")
        wall_source = walls(shuffle.get("seed"))
        rounds = []
        builder = None
        for i, event in enumerate(events):
            tag = event.tag
            if tag == "INIT":
                if builder is not None:
                    rounds.append(builder.finish())
                builder = _RoundBuilder(event.attrib, next(wall_source), len(rounds), verify)
            elif tag in IGNORED_TAGS:
                continue
            elif builder is None:
                fail(f"{tag} appears before the first INIT")
            else:
                builder.feed(tag, event.attrib, islice(events, i + 1, None))
        if builder is None:
            fail("the mjlog has no rounds")
        rounds.append(builder.finish())
        if verify:
            builder.check_final_scores()
    except PaifuError as error:
        ref = root.find("SHUFFLE").get("ref") if root.find("SHUFFLE") is not None else None
        if ref:
            raise PaifuError(f"{ref}: {error}") from error
        raise
    return Paifu({"rule": RULE, "rounds": rounds})


def convert_file(src, dst, verify=True):
    paifu = convert(src, verify)
    write_json(dst, paifu)
    return paifu


def _check_game_type(root):
    go = root.find("GO")
    if go is None:
        return
    game_type = int(go.get("type", "0"))
    if game_type & GO_SANMA:
        fail("three-player games are not supported")
    if game_type & (GO_NO_AKA | GO_NO_KUITAN) or not game_type & GO_HANCHAN:
        fail(f"GO.type {game_type:#x} is not a hanchan with red fives and open tanyao (tenhou_std)")


def _scores_by_seat(text):
    values = tile_list(text)
    return [values[i] * 100 for i in range(0, 8, 2)], [values[i + 1] * 100 for i in range(0, 8, 2)]


class _RoundBuilder:
    """Translates one round of a mjlog while replaying it, so passes and tile sources follow the Paifu rules."""

    def __init__(self, init, wall, index, verify):
        self.verify = verify
        self.index = index
        seed = tile_list(init["seed"])
        round_index, honba, kyotaku = seed[0], seed[1], seed[2]
        self.dealer = int(init["oya"])
        if round_index > 15:
            fail(f"unsupported round number {round_index}")
        if self.dealer != round_index % 4:
            fail(f"INIT.oya {self.dealer} does not match round {round_index}")
        yama, dice = wall
        self.yama = yama
        ten = [int(x) * 100 for x in init["ten"].split(",")]
        dealt = {seat: tile_list(init[f"hai{seat}"]) for seat in range(4)}
        hands = dict(dealt)
        hands[self.dealer] = hands[self.dealer] + [yama[83]]
        self.first_draw = yama[83]
        self.data = {
            "metainfo": {
                "wind": WINDS[round_index // 4],
                "round": round_index % 4 + 1,
                "honba": honba,
                "kyotaku": kyotaku,
                "scores": {WIND_KEYS[self.wind(seat)]: ten[seat] for seat in range(4)},
            },
            "tiles": {
                "initial_hands": {WIND_KEYS[self.wind(seat)]: sort_tiles(map(tile_name, hands[seat])) for seat in range(4)},
                **_split_yama(yama),
            },
            "decisions": [],
        }
        self.decisions = self.data["decisions"]
        if verify:
            self._check_deal(dealt, seed, dice)
        self.replay = RoundReplay(self.data, TENHOU_STD, index)
        self.replay.next_snapshot()
        self.doras = [seed[5]]
        self.last_draw = None
        self.last_discard = None
        self.riichi_pending = None
        self.riichi_check = None
        self.ended = False
        self.wins_left = 0
        self.win_deltas = None
        self.owari = None

    def _check_deal(self, hands, seed, dice):
        yama = self.yama
        for i in range(4):
            seat = (self.dealer + i) % 4
            dealt = [yama[135 - 4 * i - k] for k in range(4)] + [yama[119 - 4 * i - k] for k in range(4)]
            dealt += [yama[103 - 4 * i - k] for k in range(4)] + [yama[87 - i]]
            if sorted(dealt) != sorted(hands[seat]):
                self._fail(f"INIT.hai{seat} does not match the wall reproduced from SHUFFLE")
        if seed[5] != yama[5]:
            self._fail(f"INIT dora indicator {seed[5]} does not match the reproduced wall ({yama[5]})")
        if tuple(seed[3:5]) != dice:
            self._fail(f"INIT dice {seed[3:5]} do not match the reproduced wall {list(dice)}")

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

    def feed(self, tag, attrs, following):
        if self.ended:
            if tag == "AGARI" and self.wins_left:
                self.wins_left -= 1
                self._note_owari(attrs)
                return
            self._fail(f"{tag} follows the end of the round")
        if tag[0] in DRAW_TAGS and tag[1:].isdigit():
            self._deal(DRAW_TAGS.index(tag[0]), int(tag[1:]))
        elif tag[0] in DISCARD_TAGS and tag[1:].isdigit():
            self._discard(DISCARD_TAGS.index(tag[0]), int(tag[1:]), following)
        elif tag == "N":
            self._meld(int(attrs["who"]), int(attrs["m"]))
        elif tag == "REACH":
            self._reach(attrs)
        elif tag == "DORA":
            self.doras.append(int(attrs["hai"]))
        elif tag == "AGARI":
            self._agari(attrs, following)
        elif tag == "RYUUKYOKU":
            self._ryuukyoku(attrs)
        else:
            self._fail(f"unsupported tag {tag}")
        self._check_riichi_established()

    def _deal(self, seat, number):
        if number == self.first_draw and not self.decisions and seat == self.dealer and self.last_draw is None:
            self.last_draw = number
            return
        self._pass_if_pending()
        latest = self.replay.latest or {}
        if latest.get("type") not in ("deal", "replacement") or latest.get("player") != WINDS[self.wind(seat)]:
            self._fail(f"the log draws for seat {seat}, but the replay is at {latest}")
        self.last_draw = number
        if self.verify:
            replay = self.replay
            if latest["type"] == "deal":
                expected = self.yama[83 - replay.deals]
            else:
                expected = self.yama[RINSHAN_POSITIONS[replay.replacements - 1]]
            if number != expected:
                self._fail(f"seat {seat} draws tile {number} ({tile_name(number)}), but the reproduced wall gives {expected} ({latest['tile']})")
            self._check_doras()

    def _discard(self, seat, number, following):
        self._expect_player(seat)
        tile = tile_name(number)
        source = "deal" if number == self.last_draw and self.replay.drawn is not None else "hand"
        decision_type = "discard"
        if self.riichi_pending is not None:
            if self.riichi_pending != seat:
                self._fail(f"seat {self.riichi_pending} declared riichi, but seat {seat} discards")
            decision_type = "riichi_declaration"
            self.riichi_pending = None
        self.last_draw = None
        self.last_discard = number
        ends = _round_end_after(following)
        then_draw = ends is not None and ends.tag == "RYUUKYOKU" and ends.get("type") not in ("yao9", "ron3")
        self._push({"type": decision_type, "tile": tile, "from": source}, then_draw=then_draw)

    def _meld(self, seat, code):
        meld_type, tiles, called, offset = decode_meld(code)
        replay = self.replay
        if meld_type in ("chi", "pon", "open_kan"):
            if replay.phase != "call" or replay.call_kind != "discard":
                self._fail(f"{meld_type} by seat {seat} without a pending call_decision")
            discarder = (seat + offset) % 4
            if self.wind(discarder) != replay.call_from or called != self.last_discard:
                self._fail(f"seat {seat} calls tile {called} from seat {discarder}, but the last discard is tile {self.last_discard} by {WINDS[replay.call_from]}")
            own = sort_tiles(tile_name(t) for t in tiles if t != called)
            self._push({"type": meld_type, "player": WINDS[self.wind(seat)], "hands": own, "tile": tile_name(called)})
        elif meld_type == "closed_kan":
            self._expect_player(seat)
            self._push({"type": "closed_kan", "hands": sort_tiles(tile_name(t) for t in tiles)})
        else:
            self._expect_player(seat)
            self._push({"type": "added_kan", "hands": [tile_name(called)]})
        self.last_draw = None

    def _reach(self, attrs):
        seat, step = int(attrs["who"]), attrs.get("step")
        if step == "1":
            self._expect_player(seat)
            self.riichi_pending = seat
        elif step == "2":
            self.riichi_check = (seat, [int(x) * 100 for x in attrs["ten"].split(",")])
        else:
            self._fail(f"unknown REACH.step {step}")

    def _check_riichi_established(self):
        if self.riichi_check is None or not self.verify:
            return
        replay = self.replay
        if replay.phase == "call" or replay.pending_riichi is not None:
            return
        seat, ten = self.riichi_check
        self.riichi_check = None
        if not replay.riichi[self.wind(seat)]:
            self._fail(f"seat {seat}'s riichi is established in the log, but not in the replay")
        if self.replay.finished:
            return
        scores = [replay.scores[self.wind(s)] for s in range(4)]
        if scores != ten:
            self._fail(f"scores after seat {seat}'s riichi are {ten} in the log, but {scores} in the replay")

    def _agari(self, attrs, following):
        who, from_who = int(attrs["who"]), int(attrs["fromWho"])
        group = [attrs] + _following_wins(following)
        if who == from_who:
            if len(group) != 1:
                self._fail("a tsumo must have exactly one winner")
            self._expect_player(who)
            self._push({"type": "tsumo"})
        else:
            if self.replay.phase != "call":
                self._fail("ron without a pending call_decision")
            if any(int(a["fromWho"]) != from_who for a in group):
                self._fail("simultaneous wins must be on the same tile")
            self._push({"type": "ron", "players": [WINDS[self.wind(int(a["who"]))] for a in group]})
        self.ended = True
        self.wins_left = len(group) - 1
        self._note_owari(attrs)
        if self.verify:
            self._check_wins(group)

    def _check_wins(self, group):
        replay = self.replay
        summary = replay.summary
        if summary is None or replay.latest["type"] not in ("tsumo", "ron"):
            self._fail("the log has a win, but the replay does not settle one")
        first = group[0]
        honba, kyotaku = tile_list(first["ba"])
        start = self.data["metainfo"]
        if honba != start["honba"]:
            self._fail(f"AGARI.ba has honba {honba}, but the round started with {start['honba']}")
        expected_kyotaku = start["kyotaku"] + sum(replay.riichi)
        deltas = [0] * 4
        for attrs in group:
            for seat, delta in enumerate(_scores_by_seat(attrs["sc"])[1]):
                deltas[seat] += delta
            dora = [tile_name(t) for t in tile_list(attrs.get("doraHai", ""))]
            revealed = list(replay.dora_all[:replay.dora_revealed])
            if dora != revealed:
                self._fail(f"AGARI dora indicators are {dora} in the log, but {revealed} in the replay")
            ura = [tile_name(t) for t in tile_list(attrs.get("doraHaiUra", ""))]
            if ura and ura != list(replay.ura_all[:replay.dora_revealed]):
                self._fail(f"AGARI ura indicators are {ura} in the log, but {list(replay.ura_all[:replay.dora_revealed])} in the replay")
        if kyotaku != expected_kyotaku:
            self._fail(f"AGARI.ba has {kyotaku} riichi sticks, but the replay has {expected_kyotaku}")
        self._check_deltas(deltas)

    def _ryuukyoku(self, attrs):
        draw_type = attrs.get("type")
        if draw_type not in RYUUKYOKU_TYPES:
            self._fail(f"unknown RYUUKYOKU.type {draw_type}")
        replay = self.replay
        if draw_type == "ron3":
            if replay.phase != "call":
                self._fail("a triple ron draw without a pending call_decision")
            self._push(DRAW)
        elif draw_type == "yao9":
            if replay.phase != "self":
                self._fail("nine terminals outside a self decision")
            self._push(DRAW)
        elif replay.phase == "call":
            if replay.ptr < len(self.decisions):
                self.decisions.insert(replay.ptr, PASS)
                replay.next_snapshot()
            else:
                self._push(PASS, then_draw=True)
        elif replay.ptr < len(self.decisions):
            replay.next_snapshot()
        if not replay.finished:
            self._fail(f"the log ends the round in a draw ({draw_type}), but the replay does not")
        self.ended = True
        self._note_owari(attrs)
        if not self.verify:
            return
        latest = replay.latest
        if latest["type"] != "draw" or latest["draw_type"] != RYUUKYOKU_TYPES[draw_type]:
            self._fail(f"the log has a {RYUUKYOKU_TYPES[draw_type]} draw, but the replay ends in {latest}")
        if latest["draw_type"] == "exhaustive":
            ready = [WINDS[self.wind(seat)] for seat in range(4) if f"hai{seat}" in attrs]
            ready = [w for w in WINDS if w in ready]
            if ready != latest["ready_players"]:
                self._fail(f"ready players are {ready} in the log, but {latest['ready_players']} in the replay")
        self._check_deltas(_scores_by_seat(attrs["sc"])[1])

    def _check_doras(self):
        replay = self.replay
        revealed = list(replay.dora_all[:replay.dora_revealed])
        doras = [tile_name(t) for t in self.doras]
        if doras != revealed:
            self._fail(f"dora indicators are {doras} in the log, but {revealed} in the replay")

    def _check_deltas(self, log_deltas):
        summary = self.replay.summary
        replay_deltas = [summary["deltas"][self.wind(seat)] for seat in range(4)]
        if log_deltas != replay_deltas:
            self._fail(f"score changes by seat are {log_deltas} in the log, but {replay_deltas} in the replay")

    def _note_owari(self, attrs):
        if "owari" in attrs:
            self.owari = attrs["owari"]

    def finish(self):
        if not (self.replay.finished and self.ended) or self.wins_left:
            self._fail("the log and the replay disagree on where the round ends")
        return self.data

    def check_final_scores(self):
        """The last round carries owari: final scores by seat, leftover riichi sticks going to the top player."""
        if self.owari is None:
            fail("the last round has no owari (final scores)")
        final = [int(float(x)) * 100 for x in self.owari.split(",")[0::2]]
        replay = [self.replay.scores[self.wind(seat)] for seat in range(4)]
        leftover = self.replay.kyotaku * 1000
        diff = [f - r for f, r in zip(final, replay)]
        if leftover and sorted(diff) == [0, 0, 0, leftover] and replay[diff.index(leftover)] == max(replay):
            return
        if any(diff):
            fail(f"final scores by seat are {final} in owari, but {replay} in the replay with {self.replay.kyotaku} riichi sticks left")


def _round_end_after(following):
    """The first action tag after a discard if it ends the round, else None."""
    for event in following:
        if event.tag in TRANSPARENT_TAGS:
            continue
        return event if event.tag in ("AGARI", "RYUUKYOKU") else None
    return None


def _following_wins(following):
    wins = []
    for event in following:
        if event.tag in IGNORED_TAGS:
            continue
        if event.tag != "AGARI":
            break
        wins.append(event.attrib)
    return wins


def _split_yama(yama):
    """yama[135] is dealt first; live draws go downward from yama[83] (the dealer's 14th tile), yama[0:14] is the dead wall."""
    names = [tile_name(t) for t in yama]
    return {
        "wall": [names[82 - i] for i in range(TENHOU_STD.wall_size)],
        "rinshan": [names[i] for i in RINSHAN_POSITIONS],
        "dora_indicators": [names[i] for i in DORA_POSITIONS],
        "ura_indicators": [names[i] for i in URA_POSITIONS],
    }
