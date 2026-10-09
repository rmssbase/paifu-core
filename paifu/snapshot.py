import copy
from collections import Counter

from .common import (
    HONOR_START,
    WIND_KEYS,
    WINDS,
    check,
    expect_bool,
    expect_dict,
    expect_indices,
    expect_int,
    expect_keys,
    expect_list,
    expect_scores,
    expect_tile,
    expect_tiles,
    expect_wind,
    expect_winds,
    full_tile_counter,
    kinds_counts,
    load_json_input,
    tile_kind,
)
from .hand import is_agari, is_thirteen_orphans, waits, yaochu_kind_count

SNAPSHOT_TYPES = ("init", "discard_decision", "call_decision", "final")
LATEST_ACTION_TYPES = {
    "discard_decision": ("deal", "replacement", "chi", "pon"),
    "call_decision": ("discard", "riichi_declaration", "added_kan", "closed_kan"),
    "final": ("tsumo", "ron", "draw"),
}
PROCESS_YAKU = ("double_riichi", "one_shot", "after_a_kan", "robbing_a_kan")
DRAW_TYPES = ("exhaustive", "four_winds", "four_riichi", "four_kans", "three_ron", "nine_terminals")
MELD_TYPES = ("chi", "pon", "open_kan", "closed_kan", "added_kan")
KAN_TYPES = ("open_kan", "closed_kan", "added_kan")

METAINFO_ORDER = ("wind", "round", "dora_indicators", "ura_indicators", "remaining_tiles", "honba", "kyotaku", "scores")
PLAYER_ORDER = ("hand", "river", "tsumogiri_indices", "called_indices", "riichi", "riichi_declaration_index", "melds")
MELD_ORDER = ("type", "tiles", "called_tile", "from")
LATEST_ACTION_ORDER = ("type", "player", "players", "tile", "yaku", "draw_type", "ready_players")

WALL_TILES = 69
LIVE_TILES = 122
DEFAULT_TOTAL_POINTS = 100000


class Snapshot:
    """A validated Snapshot. Unknown information (e.g. other players' hands) may be omitted."""

    def __init__(self, data=None, total_points=DEFAULT_TOTAL_POINTS):
        self._data = None
        if data is not None:
            self.Init(data, total_points)

    def Init(self, data, total_points=DEFAULT_TOTAL_POINTS):
        self._data = validate_snapshot(load_json_input(data), total_points)
        return self

    def Dump(self):
        check(self._data is not None, "Snapshot is not initialized")
        return copy.deepcopy(self._data)

    @property
    def type(self):
        return self._data["type"]

    @property
    def latest_action(self):
        return copy.deepcopy(self._data.get("latest_action"))

    @property
    def metainfo(self):
        return copy.deepcopy(self._data["metainfo"])

    @property
    def players(self):
        return copy.deepcopy(self._data["players"])

    def __repr__(self):
        if self._data is None:
            return "Snapshot()"
        latest = self._data.get("latest_action")
        return f"Snapshot(type={self.type!r}, latest_action={latest!r})"


def validate_snapshot(obj, total_points=DEFAULT_TOTAL_POINTS):
    expect_dict(obj, "Snapshot")
    check("type" in obj, "Snapshot is missing fields: type")
    snapshot_type = obj["type"]
    check(snapshot_type in SNAPSHOT_TYPES, f"Snapshot.type is invalid: {snapshot_type!r}")
    if snapshot_type == "init":
        check("latest_action" not in obj, "init must not have latest_action")
        expect_keys(obj, "Snapshot", ("type", "metainfo", "players"))
    else:
        expect_keys(obj, "Snapshot", ("type", "latest_action", "metainfo", "players"))

    result = {"type": snapshot_type}
    if snapshot_type != "init":
        result["latest_action"] = _validate_latest_action(snapshot_type, obj["latest_action"])
    result["metainfo"] = _validate_metainfo(obj["metainfo"], total_points)
    result["players"] = _validate_players(obj["players"])
    _cross_check(result)
    return result


def _ordered(obj, order):
    return {key: obj[key] for key in order if key in obj}


def _validate_metainfo(meta, total_points):
    path = "metainfo"
    expect_keys(
        meta,
        path,
        ("wind", "round", "remaining_tiles", "honba", "kyotaku", "scores"),
        ("dora_indicators", "ura_indicators"),
    )
    meta = {k: v for k, v in meta.items() if v is not None or k not in ("dora_indicators", "ura_indicators")}
    expect_wind(meta["wind"], f"{path}.wind")
    expect_int(meta["round"], f"{path}.round", 1, 4)
    if "dora_indicators" in meta:
        expect_tiles(meta["dora_indicators"], f"{path}.dora_indicators")
        check(1 <= len(meta["dora_indicators"]) <= 5, f"{path}.dora_indicators must have 1 to 5 tiles")
    if "ura_indicators" in meta:
        expect_tiles(meta["ura_indicators"], f"{path}.ura_indicators")
        check(len(meta["ura_indicators"]) <= 5, f"{path}.ura_indicators must have at most 5 tiles")
        if "dora_indicators" in meta:
            check(
                len(meta["ura_indicators"]) <= len(meta["dora_indicators"]),
                f"{path}.ura_indicators must not outnumber dora_indicators",
            )
    expect_int(meta["remaining_tiles"], f"{path}.remaining_tiles", 0, WALL_TILES)
    expect_int(meta["honba"], f"{path}.honba", 0)
    expect_int(meta["kyotaku"], f"{path}.kyotaku", 0)
    meta["scores"] = expect_scores(meta["scores"], f"{path}.scores")
    total = sum(meta["scores"].values()) + meta["kyotaku"] * 1000
    check(total == total_points, f"points are not conserved: scores plus kyotaku add up to {total}, expected {total_points}")
    return _ordered(meta, METAINFO_ORDER)


def _validate_players(players):
    expect_keys(players, "players", WIND_KEYS)
    return {key: _validate_player(players[key], f"players.{key}", i) for i, key in enumerate(WIND_KEYS)}


def _validate_player(player, path, owner):
    expect_keys(
        player,
        path,
        ("river", "riichi", "melds"),
        ("hand", "tsumogiri_indices", "called_indices", "riichi_declaration_index"),
    )
    player = {k: v for k, v in player.items() if v is not None or k in ("river", "riichi", "melds")}
    if "hand" in player:
        expect_tiles(player["hand"], f"{path}.hand", sorted_required=True)
    river = expect_tiles(player["river"], f"{path}.river")
    for key in ("tsumogiri_indices", "called_indices"):
        if key in player:
            expect_indices(player[key], f"{path}.{key}", len(river))
    expect_bool(player["riichi"], f"{path}.riichi")
    if "riichi_declaration_index" in player:
        check(player["riichi"], f"{path}.riichi_declaration_index requires riichi to be true")
        expect_int(player["riichi_declaration_index"], f"{path}.riichi_declaration_index", 0, len(river) - 1)
    melds = expect_list(player["melds"], f"{path}.melds")
    check(len(melds) <= 4, f"{path}.melds must have at most 4 melds")
    player["melds"] = [_validate_meld(m, f"{path}.melds[{i}]", owner) for i, m in enumerate(melds)]
    if player["riichi"]:
        check(
            all(m["type"] == "closed_kan" for m in player["melds"]),
            f"{path} is in riichi but has melds other than closed kans",
        )
    return _ordered(player, PLAYER_ORDER)


def _validate_meld(meld, path, owner):
    expect_dict(meld, path)
    check(meld.get("type") in MELD_TYPES, f"{path}.type is invalid: {meld.get('type')!r}")
    meld_type = meld["type"]
    if meld_type == "closed_kan":
        expect_keys(meld, path, ("type", "tiles"))
    else:
        expect_keys(meld, path, ("type", "tiles", "called_tile", "from"))
    tiles = expect_tiles(meld["tiles"], f"{path}.tiles", sorted_required=True)
    kinds = [tile_kind(t) for t in tiles]
    if meld_type == "chi":
        check(
            len(tiles) == 3 and kinds[0] < HONOR_START and kinds[0] // 9 == kinds[2] // 9
            and kinds == [kinds[0], kinds[0] + 1, kinds[0] + 2],
            f"{path} is not a valid sequence",
        )
    elif meld_type == "pon":
        check(len(tiles) == 3 and len(set(kinds)) == 1, f"{path} is not a valid triplet")
    else:
        check(len(tiles) == 4 and len(set(kinds)) == 1, f"{path} is not a valid kan")
    if meld_type != "closed_kan":
        expect_tile(meld["called_tile"], f"{path}.called_tile")
        check(meld["called_tile"] in tiles, f"{path}.called_tile is not in tiles")
        source = WINDS.index(expect_wind(meld["from"], f"{path}.from"))
        check(source != owner, f"{path}.from must not be the owner")
        if meld_type == "chi":
            check(source == (owner - 1) % 4, f"{path} can only chi from the previous player")
    return _ordered(meld, MELD_ORDER)


def _validate_yaku_list(value, path, forbidden):
    expect_list(value, path)
    for i, name in enumerate(value):
        check(name in PROCESS_YAKU, f"{path}[{i}] is not a recordable process yaku: {name!r}")
        check(name != forbidden, f"{path}[{i}] cannot be {forbidden}")
    check(len(set(value)) == len(value), f"{path} must not repeat a yaku")
    return list(value)


def _validate_latest_action(snapshot_type, action):
    path = "latest_action"
    expect_dict(action, path)
    allowed = LATEST_ACTION_TYPES[snapshot_type]
    action_type = action.get("type")
    check(action_type in allowed, f"latest_action.type of {snapshot_type} must be one of {', '.join(allowed)}: {action_type!r}")
    if action_type in ("deal", "replacement", "discard", "riichi_declaration", "added_kan", "closed_kan"):
        expect_keys(action, path, ("type", "player", "tile"))
    elif action_type in ("chi", "pon"):
        expect_keys(action, path, ("type", "player"))
    elif action_type == "tsumo":
        expect_keys(action, path, ("type", "player", "tile", "yaku"))
        _validate_yaku_list(action["yaku"], f"{path}.yaku", "robbing_a_kan")
    elif action_type == "ron":
        expect_keys(action, path, ("type", "players", "tile", "yaku"))
        expect_winds(action["players"], f"{path}.players", allow_empty=False)
        check(len(action["players"]) <= 3, f"{path}.players must have at most 3 players")
        expect_list(action["yaku"], f"{path}.yaku")
        check(len(action["yaku"]) == len(action["players"]), f"{path}.yaku must match players one to one")
        for i, yaku in enumerate(action["yaku"]):
            _validate_yaku_list(yaku, f"{path}.yaku[{i}]", "after_a_kan")
    else:
        check(action.get("draw_type") in DRAW_TYPES, f"{path}.draw_type is invalid: {action.get('draw_type')!r}")
        if action["draw_type"] == "exhaustive":
            expect_keys(action, path, ("type", "draw_type", "ready_players"))
            ready = expect_winds(action["ready_players"], f"{path}.ready_players")
            check(ready == [w for w in WINDS if w in ready], f"{path}.ready_players must be in E, S, W, N order")
        else:
            expect_keys(action, path, ("type", "draw_type"))
    if "player" in action:
        expect_wind(action["player"], f"{path}.player")
    if "tile" in action:
        expect_tile(action["tile"], f"{path}.tile")
    return _ordered(action, LATEST_ACTION_ORDER)


def _cross_check(snapshot):
    snapshot_type = snapshot["type"]
    action = snapshot.get("latest_action")
    action_type = action["type"] if action else None
    meta = snapshot["metainfo"]
    players = [snapshot["players"][key] for key in WIND_KEYS]
    nine_terminals = action_type == "draw" and action["draw_type"] == "nine_terminals"

    if snapshot_type == "init":
        holders = {0}
    elif snapshot_type == "discard_decision" or action_type == "tsumo":
        holders = {WINDS.index(action["player"])}
    else:
        holders = set()

    for i, player in enumerate(players):
        path = f"players.{WIND_KEYS[i]}"
        meld_count = len(player["melds"])
        hand = player.get("hand")
        if nine_terminals:
            if hand is not None:
                check(len(hand) + 3 * meld_count in (13, 14), f"{path} has an invalid number of tiles")
            continue
        expected = 14 if i in holders else 13
        if hand is not None:
            check(
                len(hand) + 3 * meld_count == expected,
                f"{path} has {len(hand)} tiles in hand and {meld_count} melds, which should amount to {expected} tiles",
            )
        else:
            check(expected - 3 * meld_count >= 1, f"{path} has too many melds")
    if nine_terminals:
        known_14 = [i for i, p in enumerate(players) if "hand" in p and len(p["hand"]) + 3 * len(p["melds"]) == 14]
        check(len(known_14) <= 1, "at most one player holds 14 tiles in a nine terminals draw")
        if all("hand" in p for p in players):
            check(len(known_14) == 1, "one player must hold 14 tiles in a nine terminals draw")
        for i in known_14:
            check(yaochu_kind_count(kinds_counts(players[i]["hand"])) >= 9, "the nine terminals player has fewer than nine kinds of terminals and honors")
    extra = 1 if holders or nine_terminals else 0

    _check_tile_counts(players, meta)

    kan_count = sum(1 for p in players for m in p["melds"] if m["type"] in KAN_TYPES)
    check(kan_count <= 4, "there must be at most 4 kans on the table")
    kan_called = snapshot_type == "call_decision" and action_type in ("added_kan", "closed_kan")
    pending_replacement = kan_called or action_type == "ron"
    replaced = kan_count - (1 if pending_replacement and kan_count else 0)
    check(meta["remaining_tiles"] <= WALL_TILES - replaced, "remaining_tiles contradicts the number of kans")
    if "dora_indicators" in meta:
        dora_count = len(meta["dora_indicators"])
        allowed = {max(kan_count, 1), kan_count + 1}
        if kan_called and kan_count >= 2:
            allowed.add(kan_count - 1)
        check(dora_count in allowed, "the number of dora indicators contradicts the number of kans")

    if all("called_indices" in p for p in players):
        visible = 52 + extra
        for p in players:
            visible += sum(len(m["tiles"]) - 3 for m in p["melds"])
            visible += len(p["river"]) - len(p["called_indices"])
        check(
            visible == LIVE_TILES - meta["remaining_tiles"],
            f"tiles drawn so far contradict remaining_tiles: {visible} tiles in play, remaining_tiles is {meta['remaining_tiles']}",
        )

    if snapshot_type == "init":
        for i, p in enumerate(players):
            path = f"players.{WIND_KEYS[i]}"
            check(not p["river"] and not p["melds"] and not p["riichi"], f"{path} must have no river, melds or riichi at init")
        check(meta["remaining_tiles"] == WALL_TILES, f"remaining_tiles must be {WALL_TILES} at init")

    ura = meta.get("ura_indicators") or []
    if ura:
        winners = []
        if action_type == "tsumo":
            winners = [action["player"]]
        elif action_type == "ron":
            winners = action["players"]
        check(
            snapshot_type == "final" and any(players[WINDS.index(w)]["riichi"] for w in winners),
            "ura indicators are only revealed in a final won by a player in riichi",
        )
        if "dora_indicators" in meta:
            check(len(ura) == len(meta["dora_indicators"]), "ura indicators must match the dora indicators in number")

    for i, p in enumerate(players):
        hand = p.get("hand")
        if p["riichi"] and hand is not None:
            counts = kinds_counts(hand)
            if len(hand) + 3 * len(p["melds"]) == 13:
                check(waits(counts), f"players.{WIND_KEYS[i]} is in riichi but not ready")
            elif snapshot_type == "discard_decision" and action_type in ("deal", "replacement"):
                counts[tile_kind(action["tile"])] -= 1
                check(waits(counts), f"players.{WIND_KEYS[i]} is in riichi but not ready")

    if action is not None:
        _check_latest_action(snapshot_type, action, players, meta)


def _check_tile_counts(players, meta):
    counter = Counter()
    for p in players:
        counter.update(p.get("hand", []))
        for meld in p["melds"]:
            counter.update(meld["tiles"])
        if "called_indices" in p:
            called = set(p["called_indices"])
            counter.update(t for j, t in enumerate(p["river"]) if j not in called)
    counter.update(meta.get("dora_indicators", []))
    counter.update(meta.get("ura_indicators", []))
    full = full_tile_counter()
    for tile, count in counter.items():
        check(count <= full[tile], f"tile {tile} appears {count} times, more than the {full[tile]} in the set")


def _check_latest_action(snapshot_type, action, players, meta):
    action_type = action["type"]
    if "player" in action:
        actor = players[WINDS.index(action["player"])]
    if action_type in ("deal", "replacement"):
        if "hand" in actor:
            check(action["tile"] in actor["hand"], "latest_action.tile is not in the player's hand")
    elif action_type in ("chi", "pon"):
        check(actor["melds"] and actor["melds"][-1]["type"] == action_type, f"the player's last meld must be a {action_type}")
    elif action_type in ("discard", "riichi_declaration"):
        river = actor["river"]
        check(river and river[-1] == action["tile"], "latest_action.tile must be the last tile of the player's river")
        if "called_indices" in actor:
            check(len(river) - 1 not in actor["called_indices"], "the tile just discarded cannot have been called yet")
        if action_type == "riichi_declaration":
            check(not actor["riichi"], "riichi is not established while the declaration tile is on the table")
    elif action_type == "added_kan":
        check(
            any(m["type"] == "added_kan" and action["tile"] in m["tiles"] for m in actor["melds"]),
            "the player has no added kan containing latest_action.tile",
        )
    elif action_type == "closed_kan":
        check(
            actor["melds"] and actor["melds"][-1]["type"] == "closed_kan" and action["tile"] in actor["melds"][-1]["tiles"],
            "the player's last meld must be a closed kan containing latest_action.tile",
        )
        others = [p for p in players if p is not actor]
        if all("hand" in p for p in others):
            check(
                any(is_thirteen_orphans(kinds_counts(p["hand"] + [action["tile"]])) for p in others),
                "a closed kan call_decision needs another player who can rob it with thirteen orphans",
            )
    elif action_type == "tsumo":
        _check_process_yaku(actor, action["yaku"])
        if "hand" in actor:
            check(action["tile"] in actor["hand"], "the tsumo tile is not in the winner's hand")
            check(is_agari(kinds_counts(actor["hand"])), "the tsumo player's hand is not a winning hand")
    elif action_type == "ron":
        for wind, yaku in zip(action["players"], action["yaku"]):
            winner = players[WINDS.index(wind)]
            _check_process_yaku(winner, yaku)
            if "hand" in winner:
                check(is_agari(kinds_counts(winner["hand"] + [action["tile"]])), f"{wind}'s hand plus the winning tile is not a winning hand")
    elif action_type == "draw" and action["draw_type"] == "exhaustive":
        check(meta["remaining_tiles"] == 0, "remaining_tiles must be 0 in an exhaustive draw")
        for i, p in enumerate(players):
            if "hand" not in p:
                continue
            ready = bool(waits(kinds_counts(p["hand"])))
            check(ready == (WINDS[i] in action["ready_players"]), f"{WINDS[i]}'s ready state contradicts ready_players")


def _check_process_yaku(player, yaku):
    if "one_shot" in yaku or "double_riichi" in yaku:
        check(player["riichi"], "one_shot and double_riichi require the winner to be in riichi")
