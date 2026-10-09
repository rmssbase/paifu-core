import copy

from .common import (
    DRAGON_KINDS,
    HONOR_START,
    WIND_KEYS,
    WIND_KINDS,
    WINDS,
    YAOCHU_KINDS,
    PaifuError,
    kinds_counts,
    remove_tiles,
    sort_tiles,
    tile_kind,
    tile_sort_key,
    wind_kind,
)
from .hand import is_thirteen_orphans, waits, yaochu_kind_count
from .scoring import WinContext, ceil100, evaluate_win
from .snapshot import Snapshot

SELF_DECISIONS = {
    "init": ("discard", "riichi_declaration", "closed_kan", "tsumo", "draw"),
    "deal": ("discard", "riichi_declaration", "closed_kan", "added_kan", "tsumo", "draw"),
    "replacement": ("discard", "riichi_declaration", "closed_kan", "added_kan", "tsumo", "draw"),
    "call": ("discard",),
}
CALL_DECISIONS = {
    "discard": ("chi", "pon", "open_kan", "ron", "pass", "draw"),
    "added_kan": ("ron", "pass"),
    "closed_kan": ("ron", "pass"),
}


class RoundReplay:
    """Replays one round of a Paifu and yields Snapshot objects one decision point at a time."""

    def __init__(self, data, rules, index):
        self.data = data
        self.rules = rules
        self.index = index
        self.reset()

    def reset(self):
        meta = self.data["metainfo"]
        tiles = self.data["tiles"]
        self.decisions = self.data["decisions"]
        self.wind = meta["wind"]
        self.round = meta["round"]
        self.honba = meta["honba"]
        self.kyotaku = meta["kyotaku"]
        self.scores = [meta["scores"][key] for key in WIND_KEYS]
        self.hands = [list(tiles["initial_hands"][key]) for key in WIND_KEYS]
        self.wall = tiles["wall"]
        self.rinshan = tiles["rinshan"]
        self.dora_all = tiles["dora_indicators"]
        self.ura_all = tiles["ura_indicators"]

        self.rivers = [[] for _ in range(4)]
        self.tsumogiri = [[] for _ in range(4)]
        self.called = [[] for _ in range(4)]
        self.melds = [[] for _ in range(4)]
        self.riichi = [False] * 4
        self.riichi_index = [None] * 4
        self.double_riichi = [False] * 4
        self.ippatsu = [False] * 4
        self.temp_furiten = [False] * 4
        self.riichi_furiten = [False] * 4
        self.discard_count = [0] * 4
        self.pao = [{} for _ in range(4)]

        self.deals = 0
        self.replacements = 0
        self.dora_revealed = 1
        self.pending_dora = 0
        self.kan_owners = []
        self.no_call_yet = True
        self.first_discards = []
        self.pending_riichi = None

        self.phase = "start"
        self.context = "init"
        self.current = 0
        self.drawn = None
        self.kuikae = set()
        self.latest = None
        self.call_kind = None
        self.call_from = None
        self.call_tile = None
        self.options = {}
        self.show_ura = False
        self.summary = None
        self.ptr = 0
        self.decision_index = None

    @property
    def finished(self):
        return self.phase == "done"

    def next_snapshot(self):
        if self.phase == "start":
            self.phase = "self"
            return self._snapshot("init")
        if self.phase == "done":
            return None
        decision = self._take_decision()
        if self.phase == "self":
            return self._apply_self(decision)
        return self._apply_call(decision)

    def _fail(self, message):
        meta = self.data["metainfo"]
        where = f"round {self.index + 1} ({meta['wind']}{meta['round']}, honba {meta['honba']})"
        if self.decision_index is not None:
            where += f", decision {self.decision_index + 1}"
        raise PaifuError(f"{where}: {message}")

    def _take_decision(self):
        if self.ptr >= len(self.decisions):
            self.decision_index = None
            self._fail("decisions ran out before the round ended")
        self.decision_index = self.ptr
        self.ptr += 1
        return self.decisions[self.decision_index]

    def _remaining(self):
        return self.rules.wall_size - self.deals - self.replacements

    def _snapshot(self, snapshot_type):
        meta = {
            "wind": self.wind,
            "round": self.round,
            "dora_indicators": list(self.dora_all[:self.dora_revealed]),
            "ura_indicators": list(self.ura_all[:self.dora_revealed]) if self.show_ura else [],
            "remaining_tiles": self._remaining(),
            "honba": self.honba,
            "kyotaku": self.kyotaku,
            "scores": {key: self.scores[i] for i, key in enumerate(WIND_KEYS)},
        }
        players = {}
        for i, key in enumerate(WIND_KEYS):
            player = {
                "hand": sort_tiles(self.hands[i]),
                "river": list(self.rivers[i]),
                "tsumogiri_indices": list(self.tsumogiri[i]),
                "called_indices": list(self.called[i]),
                "riichi": self.riichi[i],
            }
            if self.riichi[i] and self.riichi_index[i] is not None:
                player["riichi_declaration_index"] = self.riichi_index[i]
            player["melds"] = copy.deepcopy(self.melds[i])
            players[key] = player
        obj = {"type": snapshot_type}
        if self.latest is not None:
            obj["latest_action"] = copy.deepcopy(self.latest)
        obj["metainfo"] = meta
        obj["players"] = players
        try:
            return Snapshot(obj, self.rules.total_points)
        except PaifuError as error:
            self._fail(f"replay produced an invalid Snapshot: {error}")

    def _apply_self(self, decision):
        decision_type = decision["type"]
        player = self.current
        if decision_type not in SELF_DECISIONS[self.context]:
            self._fail(f"{WINDS[player]} cannot {decision_type} at this decision point")
        if decision_type in ("discard", "riichi_declaration"):
            return self._discard(player, decision)
        if decision_type == "closed_kan":
            return self._closed_kan(player, decision["hands"])
        if decision_type == "added_kan":
            return self._added_kan(player, decision["hands"][0])
        if decision_type == "tsumo":
            return self._tsumo(player)
        return self._nine_terminals(player)

    def _discard(self, player, decision):
        decision_type = decision["type"]
        tile = decision["tile"]
        source = decision["from"]
        hand = self.hands[player]
        if tile not in hand:
            self._fail(f"{WINDS[player]} does not hold {tile}")
        if source == "deal":
            if self.drawn is None:
                self._fail("there is no freshly drawn tile, so from cannot be deal")
            if tile != self.drawn:
                self._fail(f"the drawn tile is {self.drawn}, not {tile}")
        elif hand.count(tile) - (1 if self.drawn == tile else 0) < 1:
            self._fail(f"the only {tile} is the drawn tile, so from must be deal")
        if self.riichi[player] and (decision_type != "discard" or source != "deal"):
            self._fail("a player in riichi must discard the drawn tile")
        if self.context == "call" and self.rules.kuikae_forbidden and tile_kind(tile) in self.kuikae:
            self._fail(f"{tile} cannot be discarded right after the call (kuikae)")
        if decision_type == "riichi_declaration":
            self._check_riichi(player, tile)

        hand.remove(tile)
        self.rivers[player].append(tile)
        if source == "deal":
            self.tsumogiri[player].append(len(self.rivers[player]) - 1)
        first = self.discard_count[player] == 0
        self.discard_count[player] += 1
        if self.riichi[player]:
            self.ippatsu[player] = False
        self.temp_furiten[player] = False
        if first and self.no_call_yet:
            self.first_discards.append(tile_kind(tile))
        if decision_type == "riichi_declaration":
            self.pending_riichi = player
            self.double_riichi[player] = first and self.no_call_yet
        self._reveal_pending_dora()
        self.drawn = None
        self.kuikae = set()
        self.latest = {"type": decision_type, "player": WINDS[player], "tile": tile}
        self.call_kind, self.call_from, self.call_tile = "discard", player, tile
        self.options = self._call_options(player, tile, "discard")
        if self.options:
            self.phase = "call"
            return self._snapshot("call_decision")
        return self._after_discard()

    def _check_riichi(self, player, tile):
        if self.riichi[player]:
            self._fail("the player is already in riichi")
        if any(meld["type"] != "closed_kan" for meld in self.melds[player]):
            self._fail("riichi is not allowed with open melds")
        if self.scores[player] < self.rules.riichi_cost:
            self._fail(f"riichi needs at least {self.rules.riichi_cost} points")
        if self._remaining() < self.rules.riichi_min_remaining:
            self._fail(f"riichi needs at least {self.rules.riichi_min_remaining} tiles left in the wall")
        rest = remove_tiles(self.hands[player], [tile])
        if not waits(kinds_counts(rest)):
            self._fail(f"the hand is not ready after discarding {tile}, so riichi is not allowed")

    def _after_discard(self):
        player, tile = self.call_from, self.call_tile
        self._mark_skipped_wins(player, tile)
        self._establish_riichi()
        draw_type = self._abortive_draw_type()
        if draw_type is None and self._remaining() == 0:
            draw_type = "exhaustive"
        if draw_type is not None:
            decision = self._take_decision()
            if decision["type"] != "draw":
                self._fail(f"the round ends in a draw ({draw_type}) here, so the decision must be draw, got {decision['type']}")
            return self._finish_draw(draw_type)
        return self._deal((player + 1) % 4)

    def _abortive_draw_type(self):
        if all(self.riichi):
            return "four_riichi"
        if (
            self.no_call_yet
            and len(self.first_discards) == 4
            and len(set(self.first_discards)) == 1
            and self.first_discards[0] in WIND_KINDS
        ):
            return "four_winds"
        if len(self.kan_owners) == self.rules.max_kans and len(set(self.kan_owners)) > 1:
            return "four_kans"
        return None

    def _mark_skipped_wins(self, discarder, tile, players=None):
        kind = tile_kind(tile)
        for player in range(4) if players is None else players:
            if player == discarder:
                continue
            if kind in waits(kinds_counts(self.hands[player])):
                self.temp_furiten[player] = True
                if self.riichi[player]:
                    self.riichi_furiten[player] = True

    def _establish_riichi(self):
        player = self.pending_riichi
        if player is None:
            return
        self.pending_riichi = None
        self.scores[player] -= self.rules.riichi_cost
        self.kyotaku += 1
        self.riichi[player] = True
        self.riichi_index[player] = len(self.rivers[player]) - 1
        self.ippatsu[player] = True

    def _break_first_turn(self):
        self.no_call_yet = False
        self.ippatsu = [False] * 4

    def _reveal_pending_dora(self):
        self.dora_revealed = min(self.dora_revealed + self.pending_dora, self.rules.indicator_size)
        self.pending_dora = 0

    def _deal(self, player):
        tile = self.wall[self.deals]
        self.deals += 1
        self.hands[player].append(tile)
        self.drawn = tile
        self.current = player
        self.context = "deal"
        self.latest = {"type": "deal", "player": WINDS[player], "tile": tile}
        self.phase = "self"
        return self._snapshot("discard_decision")

    def _replacement(self, player):
        tile = self.rinshan[self.replacements]
        self.replacements += 1
        self.hands[player].append(tile)
        self.drawn = tile
        self.current = player
        self.context = "replacement"
        self.latest = {"type": "replacement", "player": WINDS[player], "tile": tile}
        self.phase = "self"
        return self._snapshot("discard_decision")

    def _check_can_kan(self):
        if len(self.kan_owners) >= self.rules.max_kans:
            self._fail(f"there are already {self.rules.max_kans} kans on the table")
        if self._remaining() == 0:
            self._fail("no kan is allowed after the wall is exhausted")

    def _closed_kan(self, player, tiles):
        rest = remove_tiles(self.hands[player], tiles)
        if rest is None:
            self._fail(f"{WINDS[player]} does not hold {tiles}")
        self._check_can_kan()
        kind = tile_kind(tiles[0])
        if self.riichi[player]:
            if self.drawn is None or tile_kind(self.drawn) != kind:
                self._fail("in riichi, a closed kan must use the drawn tile")
            before = remove_tiles(self.hands[player], [self.drawn])
            if waits(kinds_counts(before)) != waits(kinds_counts(rest)):
                self._fail("in riichi, a closed kan must not change the waits")
        self.hands[player] = rest
        self.melds[player].append({"type": "closed_kan", "tiles": sort_tiles(tiles)})
        self._reveal_pending_dora()
        self.dora_revealed = min(self.dora_revealed + 1, self.rules.indicator_size)
        self.drawn = None
        tile = sort_tiles(tiles)[-1]
        self.call_kind, self.call_from, self.call_tile = "closed_kan", player, tile
        self.options = self._call_options(player, tile, "closed_kan")
        if self.options:
            self.latest = {"type": "closed_kan", "player": WINDS[player], "tile": tile}
            self.phase = "call"
            return self._snapshot("call_decision")
        return self._complete_closed_kan()

    def _complete_closed_kan(self):
        player = self.call_from
        self._mark_skipped_wins(player, self.call_tile, list(self.options))
        self.kan_owners.append(player)
        self._break_first_turn()
        return self._replacement(player)

    def _added_kan(self, player, tile):
        hand = self.hands[player]
        if tile not in hand:
            self._fail(f"{WINDS[player]} does not hold {tile}")
        kind = tile_kind(tile)
        meld = next((m for m in self.melds[player] if m["type"] == "pon" and tile_kind(m["tiles"][0]) == kind), None)
        if meld is None:
            self._fail(f"{WINDS[player]} has no pon to add {tile} to")
        self._check_can_kan()
        if self.rules.reveal_pending_dora_on_kan:
            self._reveal_pending_dora()
        hand.remove(tile)
        meld["type"] = "added_kan"
        meld["tiles"] = sort_tiles(meld["tiles"] + [tile])
        self.drawn = None
        self.latest = {"type": "added_kan", "player": WINDS[player], "tile": tile}
        self.call_kind, self.call_from, self.call_tile = "added_kan", player, tile
        self.options = self._call_options(player, tile, "added_kan")
        if self.options:
            self.phase = "call"
            return self._snapshot("call_decision")
        return self._complete_added_kan()

    def _complete_added_kan(self):
        player, tile = self.call_from, self.call_tile
        self._mark_skipped_wins(player, tile)
        self.kan_owners.append(player)
        self._break_first_turn()
        self._reveal_pending_dora()
        self.pending_dora += 1
        return self._replacement(player)

    def _tsumo(self, player):
        context = self.context
        flags = {
            "rinshan": context == "replacement",
            "haitei": context == "deal" and self._remaining() == 0,
            "tenhou": context == "init",
            "chiihou": context == "deal" and player != 0 and self.discard_count[player] == 0 and self.no_call_yet,
        }
        hand = self.hands[player]
        candidates = sorted(set(hand), key=tile_sort_key) if context == "init" else [self.drawn]
        best = None
        for win_tile in candidates:
            result = self._evaluate(player, list(hand), win_tile, True, **flags)
            if result is not None and (best is None or (result.base, result.han, result.fu) > (best[0].base, best[0].han, best[0].fu)):
                best = (result, win_tile)
        if best is None:
            self._fail(f"{WINDS[player]} cannot win by tsumo with this hand")
        return self._finish_win([(player, best[0])], best[1], tsumo=True, rinshan=flags["rinshan"])

    def _nine_terminals(self, player):
        if not (self.context in ("init", "deal") and self.discard_count[player] == 0 and self.no_call_yet):
            self._fail("nine terminals can only be declared on the first uninterrupted draw")
        if yaochu_kind_count(kinds_counts(self.hands[player])) < 9:
            self._fail("nine terminals needs at least nine kinds of terminals and honors")
        return self._finish_draw("nine_terminals")

    def _evaluate(self, player, concealed, win_tile, tsumo, rinshan=False, chankan=False, haitei=False, tenhou=False, chiihou=False):
        riichi = self.riichi[player]
        ctx = WinContext(
            concealed=concealed,
            melds=self.melds[player],
            win_tile=win_tile,
            tsumo=tsumo,
            seat_wind=HONOR_START + player,
            round_wind=wind_kind(self.wind),
            riichi=riichi,
            double_riichi=riichi and self.double_riichi[player],
            ippatsu=riichi and self.ippatsu[player],
            rinshan=rinshan,
            chankan=chankan,
            haitei=haitei,
            houtei=not tsumo and not chankan and self._remaining() == 0,
            tenhou=tenhou,
            chiihou=chiihou,
            dora_indicators=list(self.dora_all[:self.dora_revealed]),
            ura_indicators=list(self.ura_all[:self.dora_revealed]) if riichi else [],
        )
        return evaluate_win(ctx, self.rules)

    def _can_ron(self, player, tile, chankan):
        hand = self.hands[player]
        player_waits = waits(kinds_counts(hand))
        if tile_kind(tile) not in player_waits:
            return False
        if self.temp_furiten[player] or self.riichi_furiten[player]:
            return False
        if any(tile_kind(t) in player_waits for t in self.rivers[player]):
            return False
        return self._evaluate(player, hand + [tile], tile, False, chankan=chankan) is not None

    def _call_options(self, discarder, tile, call_kind):
        options = {}
        kind = tile_kind(tile)
        if call_kind == "closed_kan":
            if not self.rules.kokushi_robs_closed_kan:
                return options
            for player in range(4):
                if player != discarder and is_thirteen_orphans(kinds_counts(self.hands[player] + [tile])):
                    if self._can_ron(player, tile, chankan=True):
                        options[player] = {"ron"}
            return options
        can_call = call_kind == "discard" and self._remaining() > 0
        for player in range(4):
            if player == discarder:
                continue
            available = set()
            if self._can_ron(player, tile, chankan=call_kind == "added_kan"):
                available.add("ron")
            if can_call and not self.riichi[player]:
                same = [t for t in self.hands[player] if tile_kind(t) == kind]
                if len(same) >= 2 and self._has_legal_discard(player, same[:2], {kind}):
                    available.add("pon")
                if len(same) >= 3 and len(self.kan_owners) < self.rules.max_kans:
                    available.add("open_kan")
                if player == (discarder + 1) % 4 and self._chi_shapes(player, tile):
                    available.add("chi")
            if available:
                options[player] = available
        return options

    def _has_legal_discard(self, player, used, forbidden):
        rest = remove_tiles(self.hands[player], used)
        if not self.rules.kuikae_forbidden:
            return bool(rest)
        return any(tile_kind(t) not in forbidden for t in rest)

    def _chi_forbidden(self, kind, low, high):
        forbidden = {kind}
        base = kind // 9 * 9
        if low == kind + 1 and kind + 3 <= base + 8:
            forbidden.add(kind + 3)
        if high == kind - 1 and kind - 3 >= base:
            forbidden.add(kind - 3)
        return forbidden

    def _chi_shapes(self, player, tile):
        kind = tile_kind(tile)
        if kind >= HONOR_START:
            return []
        base = kind // 9 * 9
        shapes = []
        for low, high in ((kind - 2, kind - 1), (kind - 1, kind + 1), (kind + 1, kind + 2)):
            if low < base or high > base + 8:
                continue
            low_tile = next((t for t in self.hands[player] if tile_kind(t) == low), None)
            high_tile = next((t for t in self.hands[player] if tile_kind(t) == high), None)
            if low_tile is None or high_tile is None:
                continue
            if self._has_legal_discard(player, [low_tile, high_tile], self._chi_forbidden(kind, low, high)):
                shapes.append((low, high))
        return shapes

    def _apply_call(self, decision):
        decision_type = decision["type"]
        if decision_type not in CALL_DECISIONS[self.call_kind]:
            self._fail(f"this call_decision does not accept {decision_type}")
        if decision_type == "pass":
            if self.call_kind == "added_kan":
                return self._complete_added_kan()
            if self.call_kind == "closed_kan":
                return self._complete_closed_kan()
            return self._after_discard()
        if decision_type == "ron":
            return self._ron(decision["players"])
        if decision_type == "draw":
            ron_players = [p for p, available in self.options.items() if "ron" in available]
            if not (self.rules.triple_ron_draw and len(ron_players) >= 3):
                self._fail("a call_decision can only end in draw when three players can ron under a triple-ron-draw rule")
            self.pending_riichi = None
            return self._finish_draw("three_ron")
        return self._call_meld(decision)

    def _ron(self, winds):
        winners = [WINDS.index(w) for w in winds]
        for player in winners:
            if "ron" not in self.options.get(player, ()):
                self._fail(f"{WINDS[player]} cannot ron this tile")
        self.pending_riichi = None
        if len(winners) >= 3 and self.rules.triple_ron_draw:
            return self._finish_draw("three_ron")
        chankan = self.call_kind in ("added_kan", "closed_kan")
        tile = self.call_tile
        results = [(p, self._evaluate(p, self.hands[p] + [tile], tile, False, chankan=chankan)) for p in winners]
        return self._finish_win(results, tile, tsumo=False, loser=self.call_from, chankan=chankan)

    def _call_meld(self, decision):
        decision_type = decision["type"]
        caller = WINDS.index(decision["player"])
        discarder, tile = self.call_from, self.call_tile
        if decision_type not in self.options.get(caller, ()):
            self._fail(f"{WINDS[caller]} cannot {decision_type} this tile")
        if decision["tile"] != tile:
            self._fail(f"the called tile is {tile}, but the decision says {decision['tile']}")
        used = decision["hands"]
        rest = remove_tiles(self.hands[caller], used)
        if rest is None:
            self._fail(f"{WINDS[caller]} does not hold {used}")
        kind = tile_kind(tile)
        used_kinds = sorted(tile_kind(t) for t in used)
        if decision_type == "pon":
            if used_kinds != [kind, kind]:
                self._fail("the pon tiles do not match the called tile")
            forbidden = {kind}
        elif decision_type == "open_kan":
            if used_kinds != [kind, kind, kind]:
                self._fail("the open kan tiles do not match the called tile")
            forbidden = set()
        else:
            shape = tuple(used_kinds)
            if shape not in self._chi_shapes(caller, tile):
                self._fail(f"cannot chi {tile} with {used}")
            forbidden = self._chi_forbidden(kind, *shape)
        if forbidden and self.rules.kuikae_forbidden and not any(tile_kind(t) not in forbidden for t in rest):
            self._fail("no legal discard would remain after this call (kuikae)")

        self._mark_skipped_wins(discarder, tile)
        self._establish_riichi()
        self.hands[caller] = rest
        self.called[discarder].append(len(self.rivers[discarder]) - 1)
        self.melds[caller].append(
            {"type": decision_type, "tiles": sort_tiles(used + [tile]), "called_tile": tile, "from": WINDS[discarder]}
        )
        self._break_first_turn()
        self._update_pao(caller, discarder, kind)
        if decision_type == "open_kan":
            self._reveal_pending_dora()
            self.kan_owners.append(caller)
            self.pending_dora += 1
            return self._replacement(caller)
        self.current = caller
        self.context = "call"
        self.drawn = None
        self.kuikae = forbidden
        self.latest = {"type": decision_type, "player": WINDS[caller]}
        self.phase = "self"
        return self._snapshot("discard_decision")

    def _update_pao(self, caller, discarder, kind):
        sets = [tile_kind(m["tiles"][0]) for m in self.melds[caller] if m["type"] != "chi"]
        if kind in DRAGON_KINDS and sum(1 for k in sets if k in DRAGON_KINDS) == 3:
            self.pao[caller]["big_three_dragons"] = discarder
        if kind in WIND_KINDS and sum(1 for k in sets if k in WIND_KINDS) == 4:
            self.pao[caller]["big_four_winds"] = discarder

    def _pao_split(self, player, result):
        """Return (liable player, part of the base points the liable player covers)."""
        for name, multiplier in result.yakuman:
            if name in self.rules.pao_yaku and name in self.pao[player]:
                covered = result.base if self.rules.pao_covers_composite else 8000 * multiplier
                return self.pao[player][name], covered
        return None, 0

    def _process_yaku(self, player, rinshan, chankan):
        yaku = []
        if self.riichi[player] and self.double_riichi[player]:
            yaku.append("double_riichi")
        if self.riichi[player] and self.ippatsu[player]:
            yaku.append("one_shot")
        if rinshan:
            yaku.append("after_a_kan")
        if chankan:
            yaku.append("robbing_a_kan")
        return yaku

    def _finish_win(self, results, tile, tsumo, loser=None, rinshan=False, chankan=False):
        deltas = [0] * 4
        honba_points = self.honba * 300
        if tsumo:
            winner, result = results[0]
            self._pay_tsumo(deltas, winner, result, honba_points)
            deltas[winner] += self.kyotaku * 1000
        else:
            ordered = sorted(results, key=lambda item: (item[0] - loser) % 4)
            for rank, (winner, result) in enumerate(ordered):
                self._pay_ron(deltas, winner, loser, result, honba_points if rank == 0 else 0)
            deltas[ordered[0][0]] += self.kyotaku * 1000
        for i in range(4):
            self.scores[i] += deltas[i]
        winners = [p for p, _ in results]
        self.kyotaku = 0
        self.honba = self.honba + 1 if 0 in winners else 0
        self.show_ura = any(self.riichi[p] for p in winners)
        if tsumo:
            self.latest = {
                "type": "tsumo",
                "player": WINDS[winners[0]],
                "tile": tile,
                "yaku": self._process_yaku(winners[0], rinshan, False),
            }
        else:
            self.latest = {
                "type": "ron",
                "players": [WINDS[p] for p in winners],
                "tile": tile,
                "yaku": [self._process_yaku(p, False, chankan) for p in winners],
            }
        self.summary = {"dealer_continues": 0 in winners, "results": results, "deltas": deltas}
        return self._finish()

    def _pay_tsumo(self, deltas, winner, result, honba_points):
        liable, pao_base = self._pao_split(winner, result)
        normal_base = result.base - pao_base
        dealer = winner == 0
        for payer in range(4):
            if payer == winner or not normal_base:
                continue
            amount = ceil100(normal_base * (2 if dealer or payer == 0 else 1))
            if liable is None:
                amount += honba_points // 3
            deltas[payer] -= amount
            deltas[winner] += amount
        if liable is not None:
            amount = ceil100(pao_base * (6 if dealer else 4)) + honba_points
            deltas[liable] -= amount
            deltas[winner] += amount

    def _pay_ron(self, deltas, winner, loser, result, honba_points):
        multiplier = 6 if winner == 0 else 4
        liable, pao_base = self._pao_split(winner, result)
        if liable is not None and liable != loser:
            pao_amount = ceil100(pao_base * multiplier)
            normal_amount = ceil100((result.base - pao_base) * multiplier)
            deltas[liable] -= pao_amount // 2 + honba_points
            deltas[loser] -= pao_amount - pao_amount // 2 + normal_amount
            deltas[winner] += pao_amount + normal_amount + honba_points
            return
        amount = ceil100(result.base * multiplier) + honba_points
        deltas[loser] -= amount
        deltas[winner] += amount

    def _is_ready(self, player):
        return bool(waits(kinds_counts(self.hands[player])))

    def _is_nagashi(self, player):
        river = self.rivers[player]
        return bool(river) and not self.called[player] and all(tile_kind(t) in YAOCHU_KINDS for t in river)

    def _finish_draw(self, draw_type):
        self.latest = {"type": "draw", "draw_type": draw_type}
        deltas = [0] * 4
        dealer_continues = True
        if draw_type == "exhaustive":
            ready = [p for p in range(4) if self._is_ready(p)]
            self.latest["ready_players"] = [WINDS[p] for p in ready]
            nagashi = [p for p in range(4) if self._is_nagashi(p)] if self.rules.nagashi_mangan else []
            if nagashi:
                for player in nagashi:
                    for payer in range(4):
                        if payer != player:
                            amount = 4000 if player == 0 or payer == 0 else 2000
                            deltas[payer] -= amount
                            deltas[player] += amount
            elif 0 < len(ready) < 4:
                gain, loss = 3000 // len(ready), 3000 // (4 - len(ready))
                for player in range(4):
                    deltas[player] += gain if player in ready else -loss
            dealer_continues = 0 in ready
        for i in range(4):
            self.scores[i] += deltas[i]
        self.honba += 1
        self.summary = {"dealer_continues": dealer_continues, "results": [], "deltas": deltas}
        return self._finish()

    def _finish(self):
        self.phase = "done"
        if self.ptr != len(self.decisions):
            self.decision_index = self.ptr
            self._fail("the round has ended but more decisions follow")
        return self._snapshot("final")
